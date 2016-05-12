#! /usr/bin/env python3
import argparse, sys, os, re
import gzip, glob
from operator import itemgetter
from os import path
from graph import Graph, TFGraph, EdgeSet, write_gxt
from parser import parse_minhash
from catlas import CAtlasBuilder, CAtlas
from minhash import MinHash
from rdomset import better_dvorak_reidl, calc_dominators, calc_domination_graph, dtf_step, ldo

DEBUG = True
sys.stdin

class AttributeDict(dict): 
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

def report(msg):
    print(msg)

def debug(msg):
    if DEBUG == True:
        print(msg)

def warn(msg):
    print("  Warning:",msg)

def error(msg):
    raise RuntimeError(msg)

def parse_minhash_dict(file):
    res = {}
    def add_minhash(v, hashlist):
        res[int(v)] = MinHash.from_list(hashlist)
    parse_minhash(file, add_minhash)
    return res

def read_project_file(projectpath, filename):
    """
        Attempts to read a project file. Checks whether compressed file (.gz)
        exists that otherwise matches the filename.
    """
    fullpath = path.join(projectpath, filename)
    zipped = False
    if not path.exists(fullpath):
        if not path.exists(fullpath+".gz"):
            error("Missing file {} in {}".format(filename, projectpath))
        else:
            zipped = True
            fullpath += ".gz"
            filename += ".gz" # for consistent report
    report("Found {} in {}".format(filename, projectpath))
    if zipped:
        return gzip.open(fullpath, 'rt')    
    return open(fullpath, 'r')

def load_and_compute_augg(project):
    """ 
        Returns a project.radius-dtf augmentation of project.graph.
        Loads cached augmentations from the project directory and writes
        newly computed augmentations into it.
    """
    augname = path.join(project.path,project.name+".aug.{}.ext")

    augs = {}
    for f in glob.glob(augname.format("[0-9]*")):
        d = int(f.split(".")[-2])
        augs[d] = f

    if 0 in augs:
        auggraph = TFGraph(project.graph)
        with open(augname.format("0"), 'r') as f:
            auggraph.add_arcs(EdgeSet.from_ext(f), 1)
    else:
        auggraph = ldo(project.graph)
        with open(augname.format("0"), 'w') as f:
            EdgeSet(auggraph.arcs(weight=1)).write_ext(f)

    num_arcs = auggraph.num_arcs()
    changed = True
    d = 1
    print("Augmenting", end=" ", flush=True)
    while changed and d <= project.radius:
        if d in augs:
            print("({})".format(d), end=" ", flush=True)                        
            with open(augname.format(d), 'r') as f:
                auggraph.add_arcs(EdgeSet.from_ext(f), d+1)
        else:
            print(d, end=" ", flush=True)            
            dtf_step(auggraph, d+1)
            with open(augname.format(d), 'w') as f:
                EdgeSet(auggraph.arcs(weight=d+1)).write_ext(f)            

        curr_arcs = auggraph.num_arcs() # This costs a bit so we store it
        changed = num_arcs < curr_arcs
        num_arcs = curr_arcs
        d += 1
    print("", flush=True)
    return auggraph


parser = argparse.ArgumentParser()
parser.add_argument('project', help='Project directory. Must contain a .gxt and an .mxt file with the same base name \
                                     as the directory.', type=str)
parser.add_argument('r', help="The catlas' radius.", type=int )
args = parser.parse_args()

project = AttributeDict()
project.radius = args.r

if not path.isdir(args.project):
    error("{} is not a valid pathname".format(args.project))
if not path.exists(args.project):
    error("Project directory {} does not exist".format(args.project))

project.path = args.project
project.name = path.basename(path.normpath(args.project))

report("Project {} in {}".format(project.name, project.path))

""" 
    Make sure .gxt and .mxt with the right naming conventions exist and load them 
"""

file = read_project_file(project.path, project.name+".gxt")
project.graph, project.node_attr, project.edge_attr = Graph.from_gxt(file)

if project.graph.has_loops():
    report("Graph contains loops. Removing loops for further processing.")
    project.graph.remove_loops()

report("Loaded graph with {} vertices, {} edges and {} components".format(len(project.graph),project.graph.num_edges(),project.graph.num_components()))

file = read_project_file(project.path, project.name+".mxt")
project.minhashes = parse_minhash_dict(file)

for v in project.graph:
    if v not in project.minhashes:
        warn("Vertex {} is missing minhashes".format(v))

report("Loaded minhashes for graph")


""" 
    Compute r-dominating set 
"""

report("\nDomset computation\n")

""" Compute augmentations or load them from the project directory """
project.augg = load_and_compute_augg(project)

project.domset = better_dvorak_reidl(project.augg, project.radius)

report("Computed {}-domset of size {} for graph with {} vertices".format(project.radius, len(project.domset), len(project.graph)))

project.dominators = calc_dominators(project.augg, project.domset, project.radius)

domsetsize = len(project.domset)
project.domgraph, project.domset, project.dominators, project.assignment = calc_domination_graph(project.graph, project.augg, project.domset, project.dominators, project.radius)

report("Computed {}-catlas domination graph with {} edges and {} components".format(project.radius,project.domgraph.num_edges(),project.domgraph.num_components()))
if domsetsize != len(project.domset):
    report("Increased domset to {} in order to ensure connectivity".format(len(project.domset)))
    report("Domgraph now has {} component(s)".format(project.domgraph.num_components()))


file = path.join(project.path,project.name+".domgraph."+str(project.radius)+".gxt")
f = open(file,'w')
write_gxt(f, project.domgraph)
f.close()


"""
    Compute catlas
"""

report("\nAtlas computation\n")
builder = CAtlasBuilder(project)

catlas = builder.build()

