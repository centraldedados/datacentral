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

Installation
------------

Development is very active at this moment; while we hadn't yet time to
sit down and document the steps in detail, here is a rough description
of the process:

 * Run `make install` -- this will create a virtualenv and install the
   necessary dependencies from `requirements.txt`
 * Copy the `settings.conf.sample` into `settings.conf`
 * Edit that file to specify which repositories you want to include in
   your website
 * Run `make html` to generate the HTML output
 * Now run `make serve` to run a simple webserver, and open the site
   by pointing your browser to `localhost:8000`.


TODO
----

 * Set up a generic base theme for the HTML output
 * Use [Hyde](http://pypi.python.org/pypi/hyde/0.8.4) for a more solid 
   static generator back-end