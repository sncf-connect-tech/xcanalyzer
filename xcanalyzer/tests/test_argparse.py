from unittest import TestCase

from ..argparse import parse_ignored_folders


class ParseIgnoredFoldersTests(TestCase):

    def test_parse_ignored_folders(self):
        ignored_dirpaths, ignored_dirs = parse_ignored_folders({
            'folder1/',  # Folder at any level
            '/folder2/',  # Folder at relative root level

            'folder3/folder4/',  # Folder at relative root level
            '/folder5/folder6/',  # Folder at relative root level
        })
        
        self.assertEqual(ignored_dirpaths, {
            'folder2',
            'folder3/folder4',
            'folder5/folder6',
        })
        self.assertEqual(ignored_dirs, {
            'folder1',
        })