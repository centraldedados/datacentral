#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Options:

 -c Clear local repos and clone everything again
 -o Offline, don't clone or pull remote repos

TODO:
- read scripts/ dir and run the preparation scripts

'''

from ConfigParser import SafeConfigParser
import jinja2
import git
import sys
import os
import shutil
import markdown
import json
import codecs
import click
import zipfile
from utils import csv2json
from zenlog import log

config_file = "settings.conf"
output_dir = "_output"
template_dir = "templates"
repo_dir = "repos"
datasets_dir = "datasets"
files_dir = "download"

# set up Jinja
env = jinja2.Environment(loader=jinja2.FileSystemLoader([template_dir]))


def create_index_page(packages):
    '''Generates the index page with the list of available packages.
    Accepts a list of pkg_info dicts, which are generated with the
    process_datapackage function.'''
    template = env.get_template("list.html")
    target = "index.html"
    context = {"datapackages": packages,
               "welcome_text": markdown.markdown(codecs.open("content/welcome_text.md", 'r', 'utf-8').read(), output_format="html5", encoding="UTF-8"),
               }
    contents = template.render(**context)
    f = codecs.open(os.path.join(output_dir, target), 'w', 'utf-8')
    f.write(contents)
    f.close()
    log.info("Created index.html.")


def create_api(packages):
    '''Generates a static API containing all the datapackage.json of the containing datasets.
    Accepts a list of pkg_info dicts, which are generated with the
    process_datapackage function.'''
    all_metadata = []
    for pkg_info in packages:
        pkg_dir = os.path.join(repo_dir, pkg_info['name'])
        all_metadata.append(json.loads(open(os.path.join(pkg_dir, "datapackage.json")).read()))
    with open(os.path.join(output_dir, 'api.json'), 'w') as api_file:
        json.dump(all_metadata, api_file)
    log.info("Created api.json.")


def create_dataset_page(pkg_info):
    '''Generate a single dataset page.'''
    template = env.get_template("dataset.html")
    name = pkg_info["name"]
    if not os.path.exists(os.path.join(output_dir, name)):
        os.makedirs(os.path.join(output_dir, name))

    target = "%s/index.html" % (name)

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
    log.info("Created %s." % target)


def process_datapackage(pkg_name):
    '''Reads a data package and returns a dict with its metadata. The
    items in the dict are:
        - name
        - title
        - license
        - description
        - sources
        - readme: in HTML, processed with python-markdown from README.md,
          empty if README.md does not exist)
        - datafiles: a dict that contains the contents of the "resources"
          attribute. Each resource also contains the "basename" property,
          which is the resource base filename (without preceding
          directory)
    '''
    pkg_dir = os.path.join(repo_dir, pkg_name)
    pkg_info = {}
    metadata = json.loads(open(os.path.join(pkg_dir, "datapackage.json")).read())

    # get main attributes
    pkg_info['name'] = pkg_name
    pkg_info['original_name'] = metadata['name']
    pkg_info['title'] = metadata['title']
    pkg_info['license'] = metadata.get('license')
    pkg_info['description'] = metadata['description']
    pkg_info['sources'] = metadata.get('sources')
    # process README
    readme = ""
    readme_path = os.path.join(pkg_dir, "README.md")
    pkg_info['readme_path'] = readme_path
    if not os.path.exists(readme_path):
        log.warn("No README.md file found in the data package.")
    else:
        contents = codecs.open(readme_path, 'r', 'utf-8').read()
        try:
            readme = markdown.markdown(contents, output_format="html5", encoding="UTF-8")
        except UnicodeDecodeError:
            log.critical("README.md has invalid encoding, maybe the datapackage is not UTF-8?")
            raise
    pkg_info['readme'] = readme
    # process resource/datafiles list
    for r in metadata['resources']:
        r['basename'] = os.path.basename(r['path'])
        if r.get('name'):
            title = os.path.basename(r['name'])
        else:
            # no resource name, use capitalised filename
            title = os.path.basename(r['path']).split('.')[0]
            title = title[:1].upper() + title[1:]
        r['title'] = title

    pkg_info['datafiles'] = metadata['resources']

    return pkg_info


@click.command()
@click.option('-f', '--fetch-only', help='Only clone or pull repos, do not generate HTML output.', is_flag=True, default=False)
@click.option('-o', '--offline', help='Offline mode, do not clone or pull.', is_flag=True, default=False)
def generate(offline, fetch_only):
    '''Main function that takes care of the whole process.'''
    # set up the output directory
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # set up the dir for storing repositories
    if not os.path.exists(repo_dir):
        log.info("Directory %s doesn't exist, creating it." % repo_dir)
        os.mkdir(repo_dir)
    # copy htaccess file
    shutil.copyfile('static/htaccess', os.path.join(output_dir, ".htaccess"))
    # create static dirs
    # TODO: only update changed files -- right now we regenerate the whole static dir
    css_dir = os.path.join(output_dir, "css")
    js_dir = os.path.join(output_dir, "js")
    img_dir = os.path.join(output_dir, "img")
    fonts_dir = os.path.join(output_dir, "fonts")
    if os.path.exists(css_dir):
        shutil.rmtree(css_dir)
    shutil.copytree("static/css", css_dir)
    if os.path.exists(js_dir):
        shutil.rmtree(js_dir)
    shutil.copytree("static/js", js_dir)
    if os.path.exists(img_dir):
        shutil.rmtree(img_dir)
    shutil.copytree("static/img", img_dir)
    if os.path.exists(fonts_dir):
        shutil.rmtree(fonts_dir)
    shutil.copytree("static/fonts", fonts_dir)

    # read the config file to get the datasets we want to publish
    parser = SafeConfigParser()
    parser.read(config_file)
    packages = []

    if not parser.items('repositories'):
        log.critical('No repository data in settings.conf (does it even exist?). Cannot proceed :(')
        sys.exit()
    # go through each specified dataset
    for r in parser.items('repositories'):
        name, url = r
        dir_name = os.path.join(repo_dir, name)

        # do we have a local copy?
        if os.path.isdir(dir_name):
            if not offline:
                log.info("Checking for changes in repo '%s'..." % name)
                repo = git.Repo(dir_name)
                origin = repo.remotes.origin
                try:
                    origin.fetch()
                except AssertionError:
                    # usually this fails on the first run, try again
                    origin.fetch()
                except git.exc.GitCommandError:
                    log.critical("Fetch error connecting to repository, this dataset will be ignored and not listed in the index!")
                    continue
                # connection errors can also happen if fetch succeeds but pull fails
                try:
                    result = origin.pull()[0]
                except git.exc.GitCommandError:
                    log.critical("Pull error connecting to repository, this dataset will be ignored and not listed in the index!")
                    continue
                # we get specific flags for the results Git gave us
                # and we set the "updated" var in order to signal whether to
                # copy over the new files to the download dir or not
                if result.flags & result.HEAD_UPTODATE:
                    log.info("No new changes in repo '%s'." % name)
                    updated = False
                elif result.flags & result.ERROR:
                    log.error("Error pulling from repo '%s'!" % name)
                    updated = False
                else:
                    # TODO: figure out other git-python flags and return more
                    # informative log output
                    log.info("Repo changed, updating. (returned flags: %d)" % result.flags)
                    updated = True
            else:
                log.info("Offline mode, using cached version of package %s..." % name)
                # we set updated to True in order to re-generate everything
                # FIXME: See checksum of CSV files to make sure they're new before
                # marking updated as true
                updated = True
                repo = git.Repo(dir_name)
            if fetch_only:
                # if the --fetch-only flag was set, skip to the next dataset
                continue
        else:
            if offline:
                log.warn("Package %s specified in settings but no local cache, skipping..." % name)
                continue
            else:
                log.info("We don't have repo '%s', cloning..." % name)
                repo = git.Repo.clone_from(url, dir_name)
                updated = True

        # get datapackage metadata
        pkg_info = process_datapackage(name)
        # set last updated time based on last commit, comes in Unix timestamp format so we convert
        import datetime
        d = repo.head.commit.committed_date
        last_updated = datetime.datetime.fromtimestamp(int("1284101485")).strftime('%Y-%m-%d %H:%M:%S')
        log.debug(last_updated)
        pkg_info['last_updated'] = last_updated
        # add it to the packages list for index page generation after the loop ends
        packages.append(pkg_info)
        # re-generate the dataset HTML pages
        create_dataset_page(pkg_info)
        # if repo was updated, copy over CSV/JSON/* and ZIP files to the download dir
        # (we always generate them if offline)
        if updated or offline:
            create_dataset_page(pkg_info)
            datafiles = pkg_info['datafiles']
            zipf = zipfile.ZipFile(os.path.join(output_dir, name + '.zip'), 'w')
            for d in datafiles:
                # copy CSV file
                target = os.path.join(output_dir, os.path.basename(d['path']))
                shutil.copyfile(os.path.join(dir_name, d['path']), target)
                # generate JSON version
                csv2json(target, target.replace(".csv", ".json"))
                # make zip file
                zipf.write(os.path.join(dir_name, d['path']), d['basename'], compress_type=zipfile.ZIP_DEFLATED)
            try:
                zipf.write(pkg_info['readme_path'], 'README.md')
            except OSError:
                pass
            zipf.close()

    # generate the HTML index with the list of available packages
    create_index_page(packages)
    # generate the static JSON API of the data packages
    create_api(packages)


if __name__ == "__main__":
    generate()
