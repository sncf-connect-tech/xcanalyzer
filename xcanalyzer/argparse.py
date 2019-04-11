import os

def parse_ignored_folders(input_ignored_folders):
    # Folder to ignore given as argument
    ignored_folders = set()
    for folder in input_ignored_folders:
        # Remove ending slashes from given ignored folder paths
        while folder and folder[-1] == os.path.sep:
            folder = folder[:-1]
        ignored_folders.add(folder)

    # Ignored path and folders
    ignored_dirpaths = {f for f in ignored_folders if os.path.sep in f}
    ignored_dirs = ignored_folders - ignored_dirpaths
    ignored_dirpaths = set(map(lambda f: f if f.startswith(os.path.sep) else '/{}'.format(f), ignored_dirpaths))

    return ignored_dirpaths, ignored_dirs
