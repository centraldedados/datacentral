#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Options:

 -c Clear local repos and clone everything again
 -o Offline, don't clone or pull remote repos

TODO:
- read scripts/ dir and run the preparation scripts
- 

'''

from ConfigParser import SafeConfigParser
import jinja2
import git, os, shutil
import logging
import markdown
import json
import codecs
import click
import zipfile
from pprint import pprint

config_file = "settings.conf"
output_dir = "_output"
template_dir = "templates"
repo_dir = "repos"
datasets_dir = "datasets"
files_dir = "download"


logging.basicConfig(level=logging.DEBUG)
env = jinja2.Environment(loader=jinja2.FileSystemLoader([template_dir]))

def create_index_page(packages):
    '''Generates the index page with the list of available packages.
    Accepts a list of pkg_info dicts, which are generated with the
    process_datapackage function.'''
    template = env.get_template("list.html")
    target = "index.html"
    datapackages = [p['name'] for p in packages]
    welcome_text = markdown.markdown(codecs.open("content/welcome_text.md", 'r', 'utf-8').read(), output_format="html5", encoding="UTF-8")
    contents = template.render(datapackages=packages, welcome_text=welcome_text)
    f = codecs.open(os.path.join(output_dir, target), 'w', 'utf-8')
    f.write(contents)
    f.close()
    logging.info("Created index.html.")

def create_dataset_page(pkg_info):
    '''Generate a single dataset page.'''
    template = env.get_template("dataset.html")
    name = pkg_info["name"]
    target = os.path.join("datasets/", name+".html")

    context = {"title": pkg_info["title"],
               "description": pkg_info["description"],
               "sources": pkg_info.get("sources"),
               "readme": pkg_info["readme"],
               "datafiles": pkg_info["datafiles"],
               "last_updated": pkg_info["last_updated"],
              }
    context['welcome_text'] = markdown.markdown(codecs.open("content/welcome_text.md", 'r', 'utf-8').read(), output_format="html5", encoding="UTF-8")
    contents = template.render(**context)

    f = codecs.open(os.path.join(output_dir, target), 'w', 'utf-8')
    f.write(contents)
    f.close()
    logging.info("Created %s." % target)


def process_datapackage(pkg_name):
    '''Reads a data package and returns a dict with its metadata. The items in
    the dict are:
        - name
        - title
        - license
        - description
        - readme (in HTML, processed with python-markdown from README.md, empty if README.md
          does not exist)
        - datafiles (a dict that contains the contents of the "resources" attribute)
    '''
    pkg_dir = os.path.join(repo_dir, pkg_name)
    pkg_info = {}
    metadata = json.loads(open(os.path.join(pkg_dir, "datapackage.json")).read())

    # get main attributes
    pkg_info['name'] = pkg_name
    pkg_info['title'] = metadata['title']
    pkg_info['license'] = metadata.get('licenses')
    pkg_info['description'] = metadata['description']
    pkg_info['sources'] = metadata.get('sources')
    # process README
    readme = ""
    readme_path = os.path.join(pkg_dir, "README.md")
    pkg_info['readme_path'] = readme_path
    if not os.path.exists(readme_path):
        logging.warn("No README.md file found in the data package.")
    else:
        contents = codecs.open(readme_path, 'r', 'utf-8').read()
        try:
            readme = markdown.markdown(contents, output_format="html5", encoding="UTF-8")
        except UnicodeDecodeError:
            logging.critical("README.md has invalid encoding, maybe the datapackage is not UTF-8?")
            raise
    pkg_info['readme'] = readme
    # process resource/datafiles list
    for r in metadata['resources']:
        r['basename'] = os.path.basename(r['path'])
    pkg_info['datafiles'] = metadata['resources']

    return pkg_info    

@click.command()
@click.option('-o', '--offline', help='Offline mode, do not clone or pull.', is_flag=True, default=False)
def generate(offline):
    '''Main function that takes care of the whole process.'''
    # set up the output directory
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # set up the dir for storing repositories
    if not os.path.exists(repo_dir):
        logging.info("Directory %s doesn't exist, creating it." % repo_dir)
        os.mkdir(repo_dir)
    # create dir for dataset pages
    if not os.path.exists(os.path.join(output_dir, datasets_dir)):
        os.mkdir(os.path.join(output_dir, datasets_dir))
    # create download dir for zip and csv/json/* dataset files
    if not os.path.exists(os.path.join(output_dir, files_dir)):
        os.mkdir(os.path.join(output_dir, files_dir))
    # create static dirs
    # TODO: only update changed files -- right now we regenerate the whole static dir
    shutil.rmtree(os.path.join(output_dir, "css"))
    shutil.copytree("static/css", os.path.join(output_dir, "css"))
    shutil.rmtree(os.path.join(output_dir, "js"))
    shutil.copytree("static/js", os.path.join(output_dir, "js"))
    shutil.rmtree(os.path.join(output_dir, "img"))
    shutil.copytree("static/img", os.path.join(output_dir, "img"))
    shutil.rmtree(os.path.join(output_dir, "fonts"))
    shutil.copytree("static/fonts", os.path.join(output_dir, "fonts"))

    # read the config file to get the datasets we want to publish
    parser = SafeConfigParser()
    parser.read(config_file)
    packages = []
    # go through each specified dataset

    for r in parser.items('repositories'):
        name, url = r
        dir_name = os.path.join(repo_dir, name)
  
        # do we have a local copy?
        if os.path.isdir(dir_name):
            if not offline:
                logging.info("Checking for changes in repo '%s'..." % name)
                repo = git.Repo(dir_name)
                origin = repo.remotes.origin
                try:
                    origin.fetch()
                except AssertionError:
                    # usually this fails on the first run, try again
                    origin.fetch()
                except git.exc.GitCommandError:
                    logging.critical("Error connecting to repository, this dataset will be ignored and not listed in the index!")
                result = origin.pull()[0]
                # we get specific flags for the results Git gave us
                # and we set the "updated" var in order to signal whether to
                # copy over the new files to the download dir or not 
                if result.flags & result.FAST_FORWARD:
                    logging.info("Pulled new changes to repo '%s'." % name)
                    updated = True
                elif result.flags & result.HEAD_UPTODATE:
                    logging.info("No new changes in repo '%s'." % name)
                    updated = False
                elif result.flags & result.ERROR:
                    logging.error("Error pulling from repo '%s'!" % name)
                    updated = False
                else:
                    # TODO: figure out the other git-python flags and return more
                    # informative logging output
                    logging.info("Repo changed, updating. (returned flags: %d)" % result.flags)
                    updated = True
            else:
                logging.info("Offline mode, using cached version of package %s..." % name)
                repo = git.Repo(dir_name)
        else:
            if offline:
                logging.warn("Package %s specified in settings but no local cache, skipping..." % name)
                continue
            else:
                logging.info("We don't have repo '%s', cloning..." % name)
                repo = git.Repo.clone_from(url, dir_name)
         
        # get datapackage metadata
        pkg_info = process_datapackage(name)
        # set last updated time based on last commit, comes in Unix timestamp format so we convert
        import datetime
        d = repo.head.commit.committed_date
        last_updated = datetime.datetime.fromtimestamp(int("1284101485")).strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(last_updated)
        pkg_info['last_updated'] = last_updated
        # add it to the packages list for index page generation after the loop ends
        packages.append(pkg_info)
        # if repo was updated, 1. generate the dataset HTML page and 2. copy over
        # CSV/JSON/* and ZIP files to the download dir
        if updated:
            create_dataset_page(pkg_info)
            datafiles = pkg_info['datafiles']
            zipf = zipfile.ZipFile(os.path.join(output_dir, files_dir, name+'.zip'), 'w')
            for d in datafiles:
                logging.info("Copying %s to the %s/%s dir." % (d['basename'], output_dir, files_dir))
                target = os.path.join(output_dir, files_dir, os.path.basename(d['path']))
                shutil.copyfile(os.path.join(dir_name, d['path']), target)
                zipf.write(os.path.join(dir_name, d['path']), d['basename'], compress_type=zipfile.ZIP_DEFLATED)
            try:
                zipf.write(pkg_info['readme_path'], 'README.md')
            except OSError:
                pass
            zipf.close()

    # generate the HTML index with the list of available packages
    create_index_page(packages)

if __name__ == "__main__":
    generate()


