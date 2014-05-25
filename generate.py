#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Options:

 -c Clear cache

TODO:
- copy dataset files to /datasets/
- read scripts/ dir and run the to_* scripts

'''

from ConfigParser import SafeConfigParser
from jinja2 import Environment, PackageLoader, Template
import git, os, shutil
import logging
import markdown
import json
import codecs
from pprint import pprint
logging.basicConfig(level=logging.DEBUG)

config_file = "datasets.conf"

output_dir = "_output"
template_dir = "templates"
repo_dir = "repos"
# env = Environment(loader=PackageLoader('datacentral', 'templates'))

if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.mkdir(output_dir)

if not os.path.exists(repo_dir):
    os.mkdir(repo_dir)

os.mkdir(os.path.join(output_dir, "datasets"))
os.mkdir(os.path.join(output_dir, "files"))

shutil.copytree("static/css", os.path.join(output_dir, "css"))
shutil.copytree("static/js", os.path.join(output_dir, "js"))
shutil.copytree("static/img", os.path.join(output_dir, "img"))

def create_index_page(packages):
    '''Accepts a list of pkg_info dicts.'''
    template = Template(open('templates/list.html', 'r').read())
    target = "index.html"
    datapackages = [p['name'] for p in packages]
    contents = template.render(datapackages=datapackages)

    f = open(os.path.join(output_dir, target), 'w')
    f.write(contents)
    f.close()
    logging.info("Created index.html.")

def create_dataset_page(pkg_info):
    template = Template(open('templates/dataset.html', 'r').read())
    name = pkg_info["name"]
    target = os.path.join("datasets/", name+".html")
    context = {"title": pkg_info["title"],
               "description": pkg_info["description"],
               "readme": pkg_info["readme"],
               "datasets": pkg_info["datasets"],
              }
    contents = template.render(**context)

    f = codecs.open(os.path.join(output_dir, target), 'w', 'utf-8')
    f.write(contents)
    f.close()
    logging.info("Created %s." % target)


def process_datapackage(pkg_dir):
    pkg_info = {}
    metadata = json.loads(open(os.path.join(repo_dir, pkg_dir, "datapackage.json")).read())

    pkg_info['name'] = pkg_dir
    pkg_info['title'] = metadata['title']
    pkg_info['license'] = metadata['licenses'][0]
    pkg_info['description'] = metadata['description']

    readme = ""
    readme_path = os.path.join(repo_dir, pkg_dir, "README.md")
    if not os.path.exists(readme_path):
        logging.warn("No README.md file found in the data package.")
    else:
        logging.info("README.md file found.")
        contents = open(readme_path, 'r').read()
        readme = markdown.markdown(contents, output_format="html5")
    pkg_info['readme'] = readme

    datasets = []
    for r in metadata['resources']:
        filename = os.path.join(pkg_dir, "data/", r['name'] + '.' + r['format'])
        datasets.append(filename)
    pkg_info['datasets'] = datasets

    return pkg_info    

def generate():
    parser = SafeConfigParser()
    parser.read(config_file)
    packages = []
    for s in parser.sections():
        dir_name = os.path.join(repo_dir, s)
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
            logging.info("We don't have repo '%s', cloning..." % s)
            repo = git.Repo.clone_from(remote_url, dir_name)
         
        pkg_info = process_datapackage(s)
        packages.append(pkg_info)
        create_dataset_page(pkg_info)
    create_index_page(packages)

if __name__ == "__main__":
    generate()


