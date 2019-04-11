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
        # Given
        project_parser = self.fixture.sample_xc_project_parser

        # When
        xcode_project = project_parser.object

        # Then - expected targets
        app_target = XcTarget(name='SampleiOSApp',
                              product_name='SampleiOSApp',
                              target_type=XcTarget.Type.APPLICATION)
        test_target = XcTarget(name='SampleiOSAppTests',
                               product_name='SampleiOSAppTests',
                               target_type=XcTarget.Type.TEST)
        ui_test_target = XcTarget(name='SampleiOSAppUITests',
                                  product_name='SampleiOSAppUITests',
                                  target_type=XcTarget.Type.UI_TEST)
        framework_target = XcTarget(name='SampleCore',
                                    product_name='SampleCore',
                                    target_type=XcTarget.Type.FRAMEWORK)

        # Then - assertions
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
    
    def test_xc_project_parser__gives_linked_frameworks_between_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        core_target = xcode_project.target_with_name('SampleCore')
        ui_target = xcode_project.target_with_name('SampleUI')

        self.assertTrue(core_target in ui_target.linked_frameworks)
    
    def test_xc_project_parser__gives_embed_frameworks_between_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        core_target = xcode_project.target_with_name('SampleCore')
        ui_target = xcode_project.target_with_name('SampleUI')
        app_target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(core_target in app_target.embed_frameworks)
        self.assertTrue(ui_target in app_target.embed_frameworks)
    
    # targets files

    def test_xc_project_parser__gives_source_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(target.source_files)
        self.assertTrue(XcFile('/SampleCore/SampleCore.swift') in target.source_files)
        self.assertFalse(XcFile('/SampleiOSApp/AppDelegate.swift') in target.source_files)
    
    def test_xc_project_parser__gives_intentdefinition_as_source_file(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        target = xcode_project.target_with_name('SampleUI')

        self.assertTrue(target.source_files)
        self.assertTrue(XcFile('/SampleUI/MyIntents.intentdefinition') in target.source_files)

    def test_xc_project_parser__gives_localized_intentdefinition_as_source_file(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        target = xcode_project.target_with_name('SampleUI')

        self.assertTrue(target.source_files)
        self.assertTrue(XcFile('/SampleUI/Base.lproj/LocalizedIntents.intentdefinition') in target.source_files)
        self.assertTrue(XcFile('/SampleUI/en.lproj/LocalizedIntents.strings') in target.source_files)
        self.assertTrue(XcFile('/SampleUI/fr.lproj/LocalizedIntents.strings') in target.source_files)

    def test_xc_project_parser__gives_resource_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(target.source_files)
        self.assertTrue(XcFile('/SampleiOSApp/View.xib') in target.resource_files)
        self.assertTrue(XcFile('/SampleiOSApp/Base.lproj/Main.storyboard') in target.resource_files)
        self.assertTrue(XcFile('/SampleiOSApp/en.lproj/Main.strings') in target.resource_files)
        self.assertTrue(XcFile('/SampleiOSApp/en.lproj/Localizable.strings') in target.resource_files)
        self.assertTrue(XcFile('/SampleiOSApp/fr.lproj/Localizable.strings') in target.resource_files)
        self.assertFalse(XcFile('/SampleiOSApp/AppDelegate.swift') in target.resource_files)
    
    def test_xc_project_parser__gives_header_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(target.header_files)
        self.assertTrue(XcFile('/SampleCore/SampleCore.h') in target.header_files)

    # groups

    def test_xc_project_parser__gives_root_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        groups = xcode_project.groups

        self.assertTrue(XcGroup('/SampleCore', '/SampleCore') in groups)
        self.assertTrue(XcGroup('/SampleCoreTests', '/SampleCoreTests') in groups)
        self.assertTrue(XcGroup('/SampleUI', '/SampleUI') in groups)
        self.assertTrue(XcGroup('/SampleiOSApp', '/SampleiOSApp') in groups)
    
    def test_xc_project_parser__gives_children_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        
        group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]

        self.assertTrue(XcGroup('/SampleCore/RelativeToProject', '/SampleCore/RelativeToProject') in group.groups)
        self.assertTrue(XcGroup('/SampleCore/RelativeToProjectWithoutFolder', '/SampleCore/RelativeToProjectWithoutFolder') in group.groups)
        self.assertTrue(XcGroup('/SampleCore/Normal', '/SampleCore/Normal') in group.groups)
    
    def test_xc_project_parser__gives_grand_children_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        core_group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]

        group = [g for g in core_group.groups if g.group_path == '/SampleCore/Normal'][0]

        expected_group = XcGroup('/SampleCore/Normal/GrandChildGroup', '/SampleCore/Normal/GrandChildGroup')
        self.assertTrue(expected_group in group.groups)
    
    def test_xc_project_parser__gives_variant_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        app_group = [g for g in xcode_project.groups if g.group_path == '/SampleiOSApp'][0]

        self.assertTrue(XcGroup('/SampleiOSApp/Main.storyboard', '/SampleiOSApp/Main.storyboard') in app_group.groups)
    
    def test_xc_project_parser__set_project_relative_to_true__for_project_relative_group(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        core_group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]

        normal_group = [g for g in core_group.groups if g.group_path == '/SampleCore/Normal'][0]
        project_relative_group = [g for g in core_group.groups if g.group_path == '/SampleCore/RelativeToProject'][0]
        project_relative_without_folder_group = [g for g in core_group.groups if g.group_path == '/SampleCore/RelativeToProjectWithoutFolder'][0]

        self.assertEqual(normal_group.is_project_relative, False)
        self.assertEqual(project_relative_group.is_project_relative, True)
        self.assertEqual(project_relative_without_folder_group.is_project_relative, True)

    # files

    def test_xc_project_parser__gives_root_files(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object

        files = xcode_project.files

        self.assertTrue(XcFile('/README.md') in files)

    def test_xc_project_parser__gives_files_of_root_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        
        group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]

        self.assertTrue(XcFile('/SampleCore/SampleCore.swift') in group.files)
        self.assertTrue(XcFile('/SampleCore/GhostFolder/Ghost.swift') in group.files)
    
    def test_xc_project_parser__gives_files_of_other_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.object
        
        core_group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]
        bar_group = [g for g in core_group.groups if g.group_path == '/SampleCore/RelativeToProject'][0]
        foo_group = [g for g in core_group.groups if g.group_path == '/SampleCore/RelativeToProjectWithoutFolder'][0]

        self.assertTrue(XcFile('/SampleCore/RelativeToProject/InsideRelativeToProject.swift') in bar_group.files)
        self.assertTrue(XcFile('/SampleCore/InsideRelativeToProjectWithoutFolder.swift') in foo_group.files)
