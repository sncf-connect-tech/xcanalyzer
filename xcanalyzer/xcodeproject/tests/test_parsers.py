from unittest import TestCase

import os

from ..models import XcTarget, XcGroup, XcFile
from ..parsers import XcProjectParser

from .fixtures import SampleXcodeProjectFixture, XcProjectParserFixture


class XcProjectParserTests(TestCase):

    fixture = XcProjectParserFixture()

    # __init__

    def test_instantiate_xc_project(self):
        path = SampleXcodeProjectFixture().project_folder_path
        XcProjectParser(path)
    
    # load
    
    def test_xc_project_parser_load(self):
        path = SampleXcodeProjectFixture().project_folder_path
        project_parser = XcProjectParser(path)

        project_parser.load()

    # targets

    def test_xc_project_parser__gives_xcproject_with_name(self):
        project_parser = self.fixture.sample_xc_project_parser

        self.assertTrue(project_parser.object)
        self.assertTrue(project_parser.object.name, 'SampleiOSApp')

    def test_xc_project_parser__loaded__gives_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        app_target = XcTarget(name='SampleiOSApp', target_type=XcTarget.Type.APPLICATION)
        test_target = XcTarget(name='SampleiOSAppTests', target_type=XcTarget.Type.TEST)
        ui_test_target = XcTarget(name='SampleiOSAppUITests', target_type=XcTarget.Type.UI_TEST)
        framework_target = XcTarget(name='SampleCore', target_type=XcTarget.Type.FRAMEWORK)
        self.assertTrue(app_target in xcode_project.targets)
        self.assertTrue(test_target in xcode_project.targets)
        self.assertTrue(ui_test_target in xcode_project.targets)
        self.assertTrue(framework_target in xcode_project.targets)
    
    def test_xc_project_parser__gives_dependencies_between_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        core_target = xcode_project.target_with_name('SampleCore')
        ui_target = xcode_project.target_with_name('SampleUI')
        app_target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(core_target in ui_target.dependencies)
        self.assertTrue(core_target in app_target.dependencies)
        self.assertTrue(ui_target in app_target.dependencies)
    
    # targets files

    def test_xc_project_parser__gives_source_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(target.source_files)
        self.assertTrue('/SampleCore/SampleCore.swift' in target.source_files)
        self.assertFalse('/SampleiOSApp/AppDelegate.swift' in target.source_files)

    def test_xc_project_parser__gives_resource_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(target.source_files)
        self.assertTrue('/SampleiOSApp/Base.lproj/Main.storyboard' in target.resource_files)
        self.assertTrue('/SampleiOSApp/en.lproj/Main.strings' in target.resource_files)
        self.assertFalse('/SampleiOSApp/AppDelegate.swift' in target.resource_files)

    # groups

    def test_xc_project_parser__gives_root_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        groups = xcode_project.groups

        self.assertTrue(XcGroup('SampleCore') in groups)
        self.assertTrue(XcGroup('SampleCoreTests') in groups)
        self.assertTrue(XcGroup('SampleUI') in groups)
        self.assertTrue(XcGroup('SampleiOSApp') in groups)
    
    def test_xc_project_parser__gives_children_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        
        group = [g for g in xcode_project.groups if g.name == 'SampleCore'][0]

        self.assertTrue(XcGroup('Bar') in group.groups)
        self.assertTrue(XcGroup('Foo') in group.groups)
        self.assertTrue(XcGroup('Toto') in group.groups)
    
    def test_xc_project_parser__gives_grand_children_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        core_group = [g for g in xcode_project.groups if g.name == 'SampleCore'][0]

        group = [g for g in core_group.groups if g.name == 'Toto'][0]

        self.assertTrue(XcGroup('GrandChildGroup') in group.groups)

    # files

    def test_xc_project_parser__gives_root_files(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        files = xcode_project.files

        self.assertTrue(XcFile('README.md') in files)

    def test_xc_project_parser__gives_files_of_root_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        
        group = [g for g in xcode_project.groups if g.name == 'SampleCore'][0]

        self.assertTrue(XcFile('SampleCore.swift') in group.files)
        self.assertTrue(XcFile('Tutu.swift') in group.files)
    
    def test_xc_project_parser__gives_files_of_other_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        
        core_group = [g for g in xcode_project.groups if g.name == 'SampleCore'][0]
        bar_group = [g for g in core_group.groups if g.name == 'Bar'][0]
        foo_group = [g for g in core_group.groups if g.name == 'Foo'][0]

        self.assertTrue(XcFile('Try.swift') in bar_group.files)
        self.assertTrue(XcFile('Tyty.swift') in foo_group.files)
