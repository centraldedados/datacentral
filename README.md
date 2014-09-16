Data Central
============

This is a lightweight platform to easily distribute public data.

It uses Open Knowledge's excellent Data Packages specification as a
common format to provide datasets. See the [Frictionless Data
vision](http://data.okfn.org/vision) document to understand why it's
crucial to think about dataset packaging and distribution.

The main design principle when coming up with Data Central was
portability and simplicity of deployment. It is a framework-less
approach, using Python scripts to gather and compile all datasets,
creating a static HTML web site. Static sites might not be terribly
sexy, but they're extremely useful for some purposes:

 * data workshops
 * offline work
 * easy deployment
 * portability and replication

We informally refer to this project as "the poor man's
[CKAN](http://ckan.org)".

Data Central even exposes a static JSON 'API', so that developers 
have an easy access to the available datasets and their metadata 
on the portal.

Installation and Usage
------------

1. **Install dependencies**. After cloning the repository, change 
   to the project directory and run `make install`. This will 
   create a local virtualenv and install the necessary 
   dependencies; it shouldn't be necessary to create a virtualenv 
   since the `make` commands are all set to work with the venv 
   that `make install` creates inside the Data Central dir.

2. **Edit settings**. Copy the `settings.conf.sample` file into 
   `settings.conf`, and edit it to set your options and point to 
   your data package repositories.

3. **Generate the HTML output**. Just run `make html`!

4. **Run a web server to see the output**. Now run `make serve` 
   to run a simple webserver, and open the site by pointing your 
   browser to `localhost:8002`.


TODO
----

 * Set up a generic base theme for the HTML output
 * Use [Hyde](http://pypi.python.org/pypi/hyde/0.8.4) for a more solid 
   static generator back-end
