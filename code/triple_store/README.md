# Local GraphDB triple store

This package implements Python code to instantiate a local GraphDB triple
store and manipulate and query RDF graph data using SPARQL.

This depends on a working installation of GraphDB Desktop.

## Installing GraphDB locally

1. Download the version for your system and follow the install instructions at
   [https://www.ontotext.com/products/graphdb/download](). In Ubuntu, a `.deb`
   package is available (named `graphdb-desktop_[version]_[arch].deb`).
   Double-click the downloaded file and click on `Install`.

2. The scripts provided use the default path for the `graphdb-desktop`
   application. In Ubuntu, it is located in `/opt/graphdb-desktop/bin/graphdb-desktop`.
   You can test if the installation was successful by opening a terminal and
   running the application:

```bash
/opt/graphdb-desktop/bin/graphdb-desktop
```

3. While loading, a splash screen is displayed and the server management page 
   will open in the web browser when ready. Close the application window to
   stop the server.

## Description of the files

1. The bash script `launch.sh` is used to launch GraphDB. The application path
   is for the default GraphDB Desktop installation
   (`/opt/graphdb-desktop/bin/graphdb-desktop`). If this changes, the 
   `launch.sh` script must be edited with the new path (variable 
   `GRAPH_DB_PATH`).

2. The module `graphdb.py` provides an interface class that can be used by
   Python scripts. Several utility scripts to perform specific actions (e.g., 
   loading Turtle files or clearing a repository) are provided in the 
   `./scripts` folder.

3. The bash script `test.sh` is provided to test the functionality. Unit tests
   for the interface are implemented in `./test`. The test runner will
   instantiate and close GraphDB automatically.

4. The `./config` folder contains a Turtle file with the necessary
   configuration information to create the repositories (RDF4J configuration
   template). 

## Testing the functionality

Run the unit tests to check if the triple store will work to run the scripts 
and analyses implemented in this repository:

1. If not already, create the environment (a `conda` definition file is
   present in the `\environment` folder with respect to the root of this 
   repository).

2. Activate the environment:

```bash
conda activate neao_use_case
```

3. If not there already, check into the `code/triple_store` folder with
   respect to the root of the repository:

```bash
cd code/triple_store
```
   
4. Execute the test runner:

```bash
./test.sh
```

5. The GraphDB Desktop application will launch automatically, tests will be
   run, and the application automatically closed. In your console, you should
   see all tests passing. This means that GraphDB can be instantiated and the
   triple store accessed by Python and the provided interface. These are the
   requirements for the execution of the queries implemented.
