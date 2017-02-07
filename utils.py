# Utility functions for data packages
import os, json, requests
from zenlog import log

def csv2json(sourcepath, targetpath):
    # csvkit magic
    import subprocess
    subprocess.call('csvjson %s > %s' % (sourcepath, targetpath), shell=True)

def download_file(folder, url, filename=None):
    if filename is None:
        filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(os.path.join(folder, filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush()
    return filename

def fetch_data_package(url, dir_name):
    rq = requests.get(url)
    if (rq.status_code != 200):
        log.warn("Not authorized %d at %s" % (rq.status_code, url))
        return False
    spec = rq.json()
    # check for update
    dp_filename = os.path.join(dir_name, 'datapackage.json')
    if os.path.isfile(dp_filename):
        with open(dp_filename) as f:
            cached = json.load(f)
            if cached == spec:
                log.debug("No updates")
                return False
    # create a data folder
    data_folder = os.path.join(dir_name, 'data')
    if not os.path.isdir(dir_name):
        os.makedirs(data_folder)
    # download a copy of the datapackage
    download_file(dir_name, url, 'datapackage.json')
    for res in spec['resources']:
        if 'path' in res:
            # paths override urls, for local mirrors
            basepath = "/".join(url.split('/')[:-1]) + '/'
            fn = download_file(data_folder, basepath + res['path'])
        elif 'url' in res:
            # download resource from url
            fn = download_file(data_folder, res['url'])
        else:
            # skip this resource
            log.debug("Skipping: %s" % res)
            continue
        if 'title' in res:
            log.debug('Downloaded: %s - %s' % (res['title'], fn))
            return True
