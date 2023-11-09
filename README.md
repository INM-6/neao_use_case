# Neuroelectrophysiology Analysis Ontology Use Case

Repository containing the code necessary to reproduce the results of the 
Neuroelectrophysiology Analysis Ontology (NEAO) manuscript.


## Table of contents
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Code repository](#code-repository)
  - [How to run](#how-to-run)
  - [Outputs](#outputs)
  - [Acknowledgments](#acknowledgments)
  - [License](#license)


## Prerequisites


### Clone the repository to a local folder

This repository must be cloned to a local folder. This can be done using the 
`git` CLI client:

```bash
git clone https://github.com/INM-6/neao_use_case.git
```


### Data

To run the analyses, the public experimental datasets availabe at 
[https://doi.gin.g-node.org/10.12751/g-node.f83565](https://doi.gin.g-node.org/10.12751/g-node.f83565) must be downloaded.

The scripts use the datasets in the NIX format, without the full (30 kHz)
bandwidth neural signal. The file used in the analyses with experimental data
is **i140703-001_no_raw.nix** that can be directly downloaded [here](https://gin.g-node.org/INT/multielectrode_grasp/raw/datasets_nix/i140703-001_no_raw.nix). 
You can also follow the [instructions on the GIN repository](https://gin.g-node.org/INT/multielectrode_grasp)
to download the files to a local repository folder using the `gin` client.

The NIX file must be downloaded/copied into the folder `/data` with respect
to the root of this repository. This allows running the analyses using the
`bash` script provided. If the data was downloaded using the `gin` client, a 
symbolic link can be created to the path where the GIN repository was cloned 
in your system (subfolder `datasets_nix`):

```bash
ln -s /path/to/multielectrode_grasp/datasets_nix ./data
```


## Installation


### Requirements

Project requires Python 3.9 and the following packages:

- conda
- pip
- scipy
- numpy
- matplotlib
- nixio
- neo
- elephant
- viziphant
- odml
- alpaca
- multipledispatch
- gastrodon

The code was run using Ubuntu 18.04.6 LTS 64-bit and `conda` 22.9.0.


### Environment

The environment can be created using `conda` with the template in the
`/environment` folder. For instructions on how to install `conda` in your
system, please check the `conda` [documentation](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

For convenience, the environment can be created using a `bash` script (this 
rewrites existing versions of the environment):

```bash
./create_env.sh
```

### Gephi

For visualization of provenance graphs as GEXF files, Gephi 0.9.7 (build 
202208031831) was used. The instructions for downloading and installing are
found in the [Installation](https://alpaca-prov.readthedocs.io/en/latest/install.html#external-tools-for-provenance-visualization) section of the 
[Alpaca documentation](https://alpaca-prov.readthedocs.io/).


### GraphDB Free

The use case describes how to query the provenance information structured in
RDF files and annotated with the NEAO. To integrate the provenance captured by
Alpaca during the execution of each analysis script and execute SPARQL queries,
a triple store must be available. This work used the Ontotext GraphDB Free 
edition (version 10.1.0, with RDF4J 4.2.0).

GraphDB Free needs to be installed locally in your system. To download and
install, follow the instructions on [https://www.ontotext.com/products/graphdb/download]().

In Ubuntu, the `graphdb-desktop` launch application is located in
`/opt/graphdb-desktop/bin/graphdb-desktop` by default. If installing to a 
different location, the `bash` scripts need to be modified in order to run the
analyses (details below).


## Code repository

The code is organized into subfolders inside the `/code` folder:
>> TODO

## How to run


### Activate the environment

```bash
conda activate neao_use_case
```


### Check GraphDB installation (optional)

If you wish to check if GraphDB was installed properly and the triple store
is accessible, a small test suite is provided in Python and can be run using 
`pytest`. This is located in the `/code/triple_store/test` folder.

For convenience, a `bash` script is provided. It will instantiate the GraphDB 
server, perform the tests, clean the test repositories, and close the 
application:

```bash
cd code/triple_store
./test.sh
```

If all three tests pass, GraphDB and the Python interface implemented for this
project are working properly.


### Running the analyses

The first step is to execute the different Python scripts that implement some
analyses of electrophysiology data (`/code/analyses` subfolder). A `bash`
script runs all the scripts (3 examples for PSD, 2 examples for surrogates and
the ISI histograms of artificial data) and outputs files to the
`/outputs/analyses` folder, with respect to the root of this repository:

```bash
./run_analyses.sh
```


### Inserting provenance data and ontology definitions into GraphDB

Once the analyses are run, provenance information is saved as TTL files 
together with the plots. This needs to be imported into GraphDB to be able to 
query the information using SPARQL. A `bash` script is implemented to perform
this automatically:

```bash
./insert_provenance_data.sh
```


### Executing the SPARQL queries and generating manuscript tables

After the data is imported, a `bash` script will run all SPARQL queries to 
address questions regarding the analysis and demonstrate the use of the NEAO.

This is accomplished in two steps:

1. Queries from individual SPARQL files (in `/code/queries`) are
   executed, generating CSV files with the raw query output. The CSV outputs
   are stored in the `/outputs/query_results` folder. This is accomplished
   by the `./run_queries.sh` script. By default, GraphDB is instantiated and
   closed automatically. This can be avoided by using the `running`
   argument: `./run_queries.sh running`.

2. Query outputs are transformed into visualization tables and formatted as
   LaTeX text files. These are the tables that are published in the manuscript.
   They are stored in the `/outputs/manuscript_tables` folder. This is
   accomplished by the `./generate_manuscript_tables.sh` script. 

For convenience, the whole process can be accomplished by running a single
`bash` script:

```bash
./get_manuscript_results.sh
```


## Outputs

### Analyses
>> TODO


### Tables
>> TODO


### Logs

The details of the Python and package version information are stored in the
`/outputs/analyses/environment.txt` file.

Details about the GraphDB server and GraphDB logs are stored in the
`/outputs/graphdb_logs` folder.


## Acknowledgments

This work was performed as part of the Helmholtz School for Data Science in 
Life, Earth and Energy (HDS-LEE) and received funding from the Helmholtz 
Association of German Research Centres. This project has received funding from 
the European Union’s Horizon 2020 Framework Programme for Research and 
Innovation under Specific Grant Agreements No. 785907 (Human Brain Project 
SGA2) and 945539 (Human Brain Project SGA3), and by the Helmholtz Association 
Initiative and Networking Fund under project number ZT-I-0003.


## License

BSD 3-Clause License
