import os

from ..models import XcTarget, XcProject, XcGroup, XcFile
from ..parsers import XcProjectParser


# Absolute path of this project root folder.
root_path = __file__
for i in range(0, 4):
    root_path = os.path.dirname(root_path)


# Models

class XcModelsFixture():

    def any_target(self, name='MyXcTarget', target_type=XcTarget.Type.APPLICATION):
        return XcTarget(name=name, target_type=target_type)
    
    def any_project(self):
        targets = set([self.any_target()])
        return XcProject('MyXcProject', targets=targets, groups=set(), files=set())
    
    def any_group(self):
        return XcGroup('/MyGroup', '/MyGroup')

    def any_file(self):
        return XcFile('/MyFile')
    
# Xcode sample project

class SampleXcodeProjectFixture():

    @property
    def project_folder_path(self):
        """ Absolute path of the folder containing `.xcodeproj` of the Xcode project sample contained in this project. """
        return os.path.join(root_path, 'SampleiOSApp')


# Parsers

class XcProjectParserFixture():

    @property
    def sample_xc_project_parser(self):
        path = SampleXcodeProjectFixture().project_folder_path
        project_parser = XcProjectParser(path)
        project_parser.load()

        return project_parser


# Generators

class XcProjectGraphGeneratorFixture():

    @property
    def test_build_folder(self):
        return os.path.join(root_path, 'build', 'test')

    def any_graph_filepath(self, filename):
        return os.path.join(self.test_build_folder, filename)
