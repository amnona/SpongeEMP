# SpongeEMP
## Web + REST-API server for the SpongeEMP project.
SpongeEMP is a comprehensive datatset of sea sponge microbiome samples, which is a part of the [Earth Microbiome Project](http://www.earthmicrobiome.org/). See [Paper](https://academic.oup.com/gigascience/article/6/10/gix077/4082886?login=true).

The server enables retrieving statistics regarding a given 16S V4 sequence (or set of sequences), identifying significant sponge taxa / geographic locations and sample types where this sequences is enriched in the SpongeEMP dataset.

## Uses
A running SpongeEMP server is available at: [spongeemp.com/](http://spongeemp.com/).

SpongeEMP can be used as a database for bacterial identification in the [Calour](https://github.com/amnona/calour) analysis program.

## Installation
The server can also be installed locally by the following commands:
- Install [miniconda](https://conda.io/miniconda.html) if not installed yet.
- Create a new environment for the server:
```
conda create --name SpongeEMP python=3 scipy numpy pandas flask h5py nose matplotlib
```
- Activate the environment:
```
source activate SpongeEMP
```
- Install additional required packages:
```
pip install biom-format
pip install flask-autodoc
```
- Install SpongeEMP server (or alternatively clone the repository):
```
pip install git+git://github.com/amnona/SpongeEMP
```

## Locally running a server
- Activate the SpongeEMP environment:
```
source activate SpongeEMP
```
- cd to SpongeEMP/sponge_emp directory
- Prepare the flask server:
```
export FLASK_APP=Server_Main.py
export FLASK_DEBUG=1
```
- and run the server:
```
flask run
```
- Open the web-browser to: 127.0.0.1:5000/main

## Data files
The repository contains two biom tables used by the SpongeEMP server (both located in sponge_emp/data/):

- final.withtax.biom : a [deblurred](http://msystems.asm.org/content/2/2/e00191-16?utm_source=TrendMDmSystems&utm_medium=TrendMDmSystems&utm_campaign=trendmdalljournals_0) biom table of all the SpongeEMP samples. Taxonomy has been added using the qiime [assign_taxonomy.py](http://qiime.org/scripts/assign_taxonomy.html) using RDP and GreenGenes.

- spongeemp.sub5k.biom : similar to final.withtax.biom, but rarified to 5000 reads/sample. This is what is used by the SpongeEMP server.

## Citation
Please cite [Submitted](submitted) when using results from this server.

[![Build Status](https://travis-ci.org/amnona/spongeworld.png?branch=master)](https://travis-ci.org/amnona/spongeworld)
[![Coverage Status](https://coveralls.io/repos/github/amnona/spongeworld/badge.svg)](https://coveralls.io/github/amnona/spongeworld)


