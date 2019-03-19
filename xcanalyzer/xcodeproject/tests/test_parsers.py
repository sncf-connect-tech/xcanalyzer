from unittest import TestCase

import os

from ..models import XcTarget
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

    # xcode_proj_name

    def test_xc_project_parser__gives_project_name(self):
        project_parser = self.fixture.sample_xc_project_parser

        self.assertEqual(project_parser.xcode_proj_name, 'SampleiOSApp.xcodeproj')

    # xcode_project

    def test_xc_project_parser__gives_xcproject_with_name(self):
        project_parser = self.fixture.sample_xc_project_parser

        self.assertTrue(project_parser.xcode_project)
        self.assertTrue(project_parser.xcode_project.name, 'SampleiOSApp')

    def test_xc_project_parser__loaded__gives_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xcode_project

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
        xcode_project = project_parser.xcode_project

        core_target = xcode_project.target_with_name('SampleCore')
        ui_target = xcode_project.target_with_name('SampleUI')
        app_target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(core_target in ui_target.dependencies)
        self.assertTrue(core_target in app_target.dependencies)
        self.assertTrue(ui_target in app_target.dependencies)
    
    # Target's files

    def test_xc_project_parser__gives_source_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xcode_project

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(target.source_files)
        self.assertTrue('/SampleCore/SampleCore.swift' in target.source_files)
        self.assertFalse('/SampleiOSApp/AppDelegate.swift' in target.source_files)

    def test_xc_project_parser__gives_resource_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xcode_project

        target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(target.source_files)
        self.assertTrue('/SampleiOSApp/Base.lproj/Main.storyboard' in target.resource_files)
        self.assertTrue('/SampleiOSApp/en.lproj/Main.strings' in target.resource_files)
        self.assertFalse('/SampleiOSApp/AppDelegate.swift' in target.resource_files)
