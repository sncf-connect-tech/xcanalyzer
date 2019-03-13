from unittest import TestCase

import os

from ..parsers import XcProjectParser

from .fixtures import SampleXcodeProjectFixture


class XcProjectParserTests(TestCase):

    def test_instantiate_xc_project(self):
        path = SampleXcodeProjectFixture().project_folder_path
        XcProjectParser(path)
    
    def test_xc_project_parser_loads(self):
        path = SampleXcodeProjectFixture().project_folder_path
        project_parser = XcProjectParser(path)

        project_parser.load()
