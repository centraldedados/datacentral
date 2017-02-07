# Utility functions for data packages
import os, requests

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
