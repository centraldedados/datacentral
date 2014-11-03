# Utility functions for data packages


def csv2json(sourcepath, targetpath):
    # csvkit magic
    import subprocess
    subprocess.call('csvjson %s > %s' % (sourcepath, targetpath), shell=True)
