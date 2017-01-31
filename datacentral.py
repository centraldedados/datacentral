#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Options:

 -c Clear local repos and clone everything again
 -o Offline, don't clone or pull remote repos

TODO:
- read scripts/ dir and run the preparation scripts

'''

try:
    from configparser import SafeConfigParser
except ImportError:
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
import glob
from utils import csv2json
from zenlog import log

CONFIG_FILE = "settings.conf"
OUTPUT_DIR = "_output"
REPO_DIR = "repos"
datasets_dir = "datasets"
files_dir = "download"
THEMES_DIR = "themes"

# init global vars
env = None
packages = []

# set logging level
log.level('info')


def local_and_remote_are_at_same_commit(repo, remote):
    local_commit = repo.commit()
    remote_commit = remote.fetch()[0].commit
    return local_commit.hexsha == remote_commit.hexsha


def create_index_page(packages, output_dir):
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
    log.debug("Created index.html.")


def create_contact_page(output_dir, contact_email=""):
    '''Creates a contact form page.'''
    template = env.get_template("contact.html")
    target_dir = os.path.join(output_dir, "contact/")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    target = os.path.join(target_dir, "index.html")
    context = {}
    context["contact_email"] = contact_email
    contents = template.render(**context)
    f = codecs.open(target, 'w', 'utf-8')
    f.write(contents)
    f.close()
    log.debug("Created contact page.")


def create_static_pages(output_dir):
    '''Generates a static page from each of the files contained in
    `content/pages/`.'''
    template = env.get_template("page.html")
    for f in glob.glob("content/pages/*.md"):
        page_name = f.split("/")[-1].replace(".md", "")
        target_dir = os.path.join(output_dir, "%s/" % page_name)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        target = os.path.join(target_dir, "index.html")
        context = {}
        md_content = codecs.open(f, 'r', 'utf-8').read()
        context["content"] = markdown.markdown(md_content, output_format="html5", encoding="UTF-8")
        contents = template.render(**context)
        f = codecs.open(target, 'w', 'utf-8')
        f.write(contents)
        f.close()
        log.debug("Created static page '%s'." % page_name)

        # Content images
        if os.path.exists("content/media"):
            media_dir = os.path.join(output_dir, "media")
            if os.path.exists(media_dir):
                shutil.rmtree(media_dir)
            shutil.copytree("content/media", media_dir)


def create_api(packages, output_dir, repo_dir):
    '''Generates a static API containing all the datapackage.json of the containing datasets.
    Accepts a list of pkg_info dicts, which are generated with the
    process_datapackage function.'''
    all_metadata = []
    for pkg_info in packages:
        pkg_dir = os.path.join(repo_dir, pkg_info['name'])
        all_metadata.append(json.loads(open(os.path.join(pkg_dir, "datapackage.json")).read()))
    with open(os.path.join(output_dir, 'api.json'), 'w') as api_file:
        json.dump(all_metadata, api_file)
    log.debug("Created api.json.")


def create_dataset_page(pkg_info, output_dir):
    '''Generate a single dataset page.'''
    template = env.get_template("dataset.html")
    name = pkg_info["name"]
    if not os.path.exists(os.path.join(output_dir, name)):
        os.makedirs(os.path.join(output_dir, name))

    target = "%s/index.html" % (name)

    context = {"datapkg": pkg_info}
    context['welcome_text'] = markdown.markdown(codecs.open("content/welcome_text.md", 'r', 'utf-8').read(), output_format="html5", encoding="UTF-8")
    contents = template.render(**context)

    f = codecs.open(os.path.join(output_dir, target), 'w', 'utf-8')
    f.write(contents)
    f.close()
    log.debug("Created %s." % target)

class ParseException(Exception):
    pass

def process_datapackage(pkg_name, repo_dir, repo_url):
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
    try:
        metadata = json.loads(open(os.path.join(pkg_dir, "datapackage.json")).read())
    except IOError:
        raise ParseException("datapackage.json not found")

    # get main attributes
    pkg_info['name'] = pkg_name
    pkg_info['homepage'] = repo_url
    pkg_info['original_name'] = metadata['name']
    pkg_info['title'] = metadata['title']
    pkg_info['license'] = metadata.get('license')
    if not 'description' in metadata:
        pkg_info['description'] = ""
    else:
        pkg_info['description'] = metadata['description']
    pkg_info['sources'] = metadata.get('sources') or []
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
            raise ParseException("README.md has invalid encoding, maybe the datapackage is not UTF-8?")
    pkg_info['readme'] = readme
    # process resource/datafiles list
    for r in metadata['resources']:
        if not r.get('schema'):
            log.warn("Schema missing in resource, adding blank")
            r['schema'] = { 'fields': [] }
        if not r.get('path'):
            log.warn("path missing in resource, skipping")
            log.debug(r)
            continue
        r['basename'] = os.path.basename(r['path'])
        if not r.get('title'):
            if r.get('name'):
                title = os.path.basename(r['name'])
            else:
                # no resource name, use capitalised filename
                title = os.path.basename(r['path']).split('.')[0]
                title = title[:1].upper() + title[1:]
            r['title'] = title

    pkg_info['datafiles'] = metadata['resources']

    return pkg_info


def generate(offline=False,
             fetch_only=False,
             output_dir=OUTPUT_DIR,
             theme_dir=os.path.join(THEMES_DIR, 'centraldedados'),
             repo_dir=REPO_DIR,
             config_file=CONFIG_FILE):
    '''Main function that takes care of the whole process.'''
    global env, packages
    # Read the config file
    parser = SafeConfigParser()
    parser.read(config_file)
    # Load the theme and set up Jinja
    theme_name = parser.get('ui', 'theme')
    theme_dir = os.path.join(THEMES_DIR, theme_name)
    template_dir = os.path.join(theme_dir, "templates")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader([template_dir]))

    # Set up the output directory
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # Set up the dir for storing repositories
    if not os.path.exists(repo_dir):
        log.debug("Directory %s doesn't exist, creating it." % repo_dir)
        os.mkdir(repo_dir)
    # Copy htaccess file
    shutil.copyfile(os.path.join(theme_dir, 'static/htaccess'), os.path.join(output_dir, ".htaccess"))
    # Create static dirs
    # TODO: only update changed files -- right now we regenerate the whole static dir

    # Static CSS files
    css_dir = os.path.join(output_dir, "css")
    if os.path.exists(css_dir):
        shutil.rmtree(css_dir)
    shutil.copytree(os.path.join(theme_dir, "static/css"), css_dir)
    # Static JavaScript files
    js_dir = os.path.join(output_dir, "js")
    if os.path.exists(js_dir):
        shutil.rmtree(js_dir)
    shutil.copytree(os.path.join(theme_dir, "static/js"), js_dir)
    # Theme images
    img_dir = os.path.join(output_dir, "img")
    if os.path.exists(img_dir):
        shutil.rmtree(img_dir)
    shutil.copytree(os.path.join(theme_dir, "static/img"), img_dir)
    # Fonts
    fonts_dir = os.path.join(output_dir, "fonts")
    if os.path.exists(fonts_dir):
        shutil.rmtree(fonts_dir)
    shutil.copytree(os.path.join(theme_dir, "static/fonts"), fonts_dir)

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
                repo = git.Repo(dir_name)
                origin = repo.remotes.origin
                try:
                    origin.fetch()
                except AssertionError:
                    # usually this fails on the first run, try again
                    origin.fetch()
                except git.exc.GitCommandError:
                    log.critical("%s: Fetch error, this dataset will be left out." % name)
                    continue
                # see if we have updates
                if not local_and_remote_are_at_same_commit(repo, origin):
                    log.debug("%s: Repo has new commits, updating local copy." % name)
                    updated = True
                    # connection errors can also happen if fetch succeeds but pull fails
                    try:
                        result = origin.pull()[0]
                    except git.exc.GitCommandError:
                        log.critical("%s: Pull error, this dataset will be left out." % name)
                        continue
                    if result.flags & result.ERROR:
                        log.error("%s: Pull error, but going ahead." % name)
                        updated = False
                else:
                    log.info("%s: No changes." % name)
                    updated = False
            else:
                log.debug("%s: Offline mode, using cached version." % name)
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
                log.warn("%s: No local cache, skipping." % name)
                continue
            else:
                log.info("%s: New repo, cloning." % name)
                try:
                    repo = git.Repo.clone_from(url, dir_name)
                    # For faster checkouts, one file at a time:
                    #repo = git.Repo.clone_from(url, dir_name, n=True, depth=1)
                    #repo.git.checkout("HEAD", "datapackage.json")
                except git.exc.GitCommandError as inst:
                    log.warn("%s: skipping %s" % (inst, name))
                    continue
                updated = True

        # get datapackage metadata
        try:
            pkg_info = process_datapackage(name, repo_dir, url)
        except ParseException as inst:
            log.warn("%s: skipping %s" % (inst, name))
            continue

        # set last updated time based on last commit, comes in Unix timestamp format so we convert
        import datetime
        d = repo.head.commit.committed_date
        last_updated = datetime.datetime.fromtimestamp(int(d)).strftime('%Y-%m-%d %H:%M:%S')
        pkg_info['last_updated'] = last_updated
        # add it to the packages list for index page generation after the loop ends
        packages.append(pkg_info)
        # re-generate the dataset HTML pages
        create_dataset_page(pkg_info, output_dir)
        # if repo was updated, copy over CSV/JSON/* and ZIP files to the download dir
        # (we always generate them if offline)
        if updated or offline:
            create_dataset_page(pkg_info, output_dir)
            datafiles = pkg_info['datafiles']
            zipf = zipfile.ZipFile(os.path.join(output_dir, name + '.zip'), 'w')
            for d in datafiles:
                log.info("Copying %s" % d['path'])
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

    # HTML index with the list of available packages
    create_index_page(packages, output_dir)
    # Static JSON API of the data packages
    create_api(packages, output_dir, repo_dir)
    # Static pages
    create_static_pages(output_dir)
    # Contact page
    create_contact_page(output_dir, parser.get('credentials', 'contact_email'))

    log.info("All static content is ready inside '%s'." % OUTPUT_DIR)


@click.command()
@click.option('-f', '--fetch-only', help='Only clone or pull repos, do not generate HTML output.', is_flag=True, default=False)
@click.option('-x', '--offline', help='Offline mode, do not clone or pull.', is_flag=True, default=False)
@click.option('-o', '--output-dir', help='Output directory (default is _output)', type=click.Path(), default=OUTPUT_DIR)
def main(offline, fetch_only, output_dir):
    generate(offline, fetch_only, output_dir)


if __name__ == "__main__":
    main()
