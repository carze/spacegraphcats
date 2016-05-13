# spacegraphcats

supercool stuff from DDD Barnraising

## Setup

* Install dependencies with `pip install -r requirements.txt`
* [Set up git lfs](https://git-lfs.github.com/) and initialize it with
  `git lfs install`

## Some big gxt/mxt files

Grab this:

    curl -O http://athyra.idyll.org/~t/transfer/spacegraphcats-extract.tar 

(It's about 220 MB.)

## Running the pipeline

For a pair of .gxt/.mxt files (say `eldritch.gxt` and `eldritch.mxt`) create
a matching project folder `eldritch'. The folder name must match the .gxt/.mxt name.

Run `python3 build-catlas.py /path/to/eldritch r` where *r* determines the coverage
radius. Larger *r* will create smaller atlases at the cost of precision and will
take longer to compute. Intermediate computational steps are cached in the project
director and will speed up subsequence catlas-computations.

## References

[Graph Modelling Language](https://en.wikipedia.org/wiki/Graph_Modelling_Language)
[Graph Text (GXT)](https://github.com/spacegraphcats/spacegraphcats/blob/master/spacegraphcats/parser-examples/README.md)
