import os

def parse_ignored_folders(input_ignored_folders):
    assert type(input_ignored_folders) == set

    # Check that every input_ignored_folder ends with a slash
    for folder in input_ignored_folders:
        if not len(folder) >= 2:
            raise ValueError("Given folder '{}' must have a length >=2 and must ends with a slash.".format(folder))
        if folder[-1] != '/':
            raise ValueError("Given folder '{}' must ends with a slash.".format(folder))

    # Remove ending slashes from given ignored folder paths
    ignored_folders = {f[:-1] for f in input_ignored_folders}

    for folder in ignored_folders:
        if '//' in folder:
            raise ValueError("2 consecutive slashes `//` in folder path is not supported.")

    ignored_dirs = {f for f in ignored_folders if '/' not in f}
    ignored_dirpaths = ignored_folders - ignored_dirs
    ignored_dirpaths = set(map(lambda f: f if not f.startswith('/') else f[1:], ignored_dirpaths))

    return ignored_dirpaths, ignored_dirs
