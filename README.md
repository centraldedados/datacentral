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

1. **Install dependencies**. After cloning the repository, run:
	
	$ pip show virtualenv

You can install virtualenv with:

	$ pip install --user virtualenv

Once all the dependecies are installed, change 
   to the project directory and run `make install`. This will 
   create a local virtualenv and install the necessary 
   dependencies; it shouldn't be necessary to create a virtualenv 
   since the `make` commands are all set to work with the venv 
   that `make install` creates inside the Data Central dir.

2. **Edit settings**. Edit the newly created `settings.conf`
   to set your options and point to your data package 
   repositories.

3. **Generate the HTML output**. Just run `make build`!

4. **Push the static HTML output somewhere!**. The generated
   site is placed at the `_output` directory. Just copy the contents
   to your webserver, everything's included.

5. **Run a web server to see the output**. While developing, you
   can also run `make serve` to run a simple webserver, and then
   open the site by pointing your browser to `localhost:8002`.

Running tests
-------------

Datacentral uses Nose for testing. After installing it on your system or virtualenv, just run

    nosetests tests.py
    

TODO
----

 * Set up an English language base theme for the HTML output
 * Use [Hyde](http://pypi.python.org/pypi/hyde/0.8.4) or
   [Pelican](http://getpelican.com) for a more solid static generator back-end
