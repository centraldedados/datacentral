#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Options:

 -c Clear cache

TODO:
- read scripts/ dir and run the to_* scripts

'''


from ConfigParser import SafeConfigParser
import git, os, shutil
import logging
import markdown
import json
from pprint import pprint
logging.basicConfig(level=logging.DEBUG)

config_file = "datasets.conf"

def process_datapackage(pkg_dir):
    metadata = json.loads(open(os.path.join(pkg_dir, "datapackage.json")).read())
    title = metadata['title']
    license = metadata['licenses'][0]
    description = metadata['description']

    readme = ""
    readme_path = os.path.join(pkg_dir, "README.md")
    if not os.path.exists(readme_path):
        logging.warn("No README.md file found in the data package.")
    else:
        readme = markdown.markdownFromFile(readme_path)
    print readme

parser = SafeConfigParser()
parser.read(config_file)

for s in parser.sections():
    dir_name = s
    remote_url = parser.get(s, 'url')
     
    if os.path.isdir(dir_name):
        # repo exists
        logging.info("Repo '%s' already exists, pulling changes..." % s)
        repo = git.Repo(dir_name)
        origin = repo.remotes.origin
        result = origin.pull()[0]
        if result.flags & result.HEAD_UPTODATE:
            logging.info("Repo '%s' is up to date." % s)
    else:
        repo = git.Repo.clone_from(remote_url, dir_name)
     
    process_datapackage(s)
