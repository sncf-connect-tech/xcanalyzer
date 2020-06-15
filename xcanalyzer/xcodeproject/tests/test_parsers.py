from unittest import TestCase

import json
import os

from ...language.models import SwiftType

from ..models import XcTarget, XcGroup, XcFile
from ..parsers import XcProjectParser, SwiftFileParser

from .fixtures import SampleXcodeProjectFixture, XcProjectParserFixture, SwiftCodeParserFixture


class XcProjectParserTests(TestCase):

    fixture = XcProjectParserFixture()

    # __init__

    def test_instantiate_xc_project(self):
        path = SampleXcodeProjectFixture().project_folder_path
        XcProjectParser(path, verbose=False)
    
    # load
    
    def test_xc_project_parser_load(self):
        path = SampleXcodeProjectFixture().project_folder_path
        project_parser = XcProjectParser(path, verbose=False)

        project_parser.load()

    # targets

    def test_xc_project_parser__gives_xcproject_with_name(self):
        project_parser = self.fixture.sample_xc_project_parser

        self.assertTrue(project_parser.xc_project)
        self.assertTrue(project_parser.xc_project.name, 'SampleiOSApp')

    def test_xc_project_parser__loaded__gives_targets(self):
        # Given
        project_parser = self.fixture.sample_xc_project_parser

        # When
        xcode_project = project_parser.xc_project

        # Then - expected targets
        app_target = XcTarget(name='SampleiOSApp',
                              product_name='SampleiOSApp',
                              target_type=XcTarget.Type.APPLICATION,
                              build_configurations=list())
        test_target = XcTarget(name='SampleiOSAppTests',
                               product_name='SampleiOSAppTests',
                               target_type=XcTarget.Type.TEST,
                               build_configurations=list())
        ui_test_target = XcTarget(name='SampleiOSAppUITests',
                                  product_name='SampleiOSAppUITests',
                                  target_type=XcTarget.Type.UI_TEST,
                                  build_configurations=list())
        framework_target = XcTarget(name='SampleCore',
                                    product_name='SampleCore',
                                    target_type=XcTarget.Type.FRAMEWORK,
                                    build_configurations=list())

        # Then - assertions
        self.assertTrue(app_target in xcode_project.targets)
        self.assertTrue(test_target in xcode_project.targets)
        self.assertTrue(ui_test_target in xcode_project.targets)
        self.assertTrue(framework_target in xcode_project.targets)
    
    def test_xc_project_parser__gives_dependencies_between_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        core_target = xcode_project.target_with_name('SampleCore')
        ui_target = xcode_project.target_with_name('SampleUI')
        app_target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(core_target in ui_target.dependencies)
        self.assertTrue(core_target in app_target.dependencies)
        self.assertTrue(ui_target in app_target.dependencies)
    
    def test_xc_project_parser__gives_linked_frameworks_between_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        core_target = xcode_project.target_with_name('SampleCore')
        ui_target = xcode_project.target_with_name('SampleUI')

        self.assertTrue(core_target in ui_target.linked_frameworks)
    
    def test_xc_project_parser__gives_embed_frameworks_between_targets(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        core_target = xcode_project.target_with_name('SampleCore')
        ui_target = xcode_project.target_with_name('SampleUI')
        app_target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(core_target in app_target.embed_frameworks)
        self.assertTrue(ui_target in app_target.embed_frameworks)
    
    # targets files

    def test_xc_project_parser__gives_source_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(target.source_files)
        self.assertTrue(XcFile('/SampleCore/SampleCore.swift') in target.source_files)
        self.assertFalse(XcFile('/SampleiOSApp/AppDelegate.swift') in target.source_files)
    
    def test_xc_project_parser__reduces_double_dot_path_parts__for_files__at_root(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(XcFile('/ViewBadPlaced.xib') in target.resource_files)
    
    def test_xc_project_parser__reduces_double_dot_path_parts__for_files__at_root__and_in_subgroup(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(XcFile('/BadPlacedRootFile.swift') in target.source_files)
    
    def test_xc_project_parser__reduces_double_dot_path_parts__for_files(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(XcFile('/BadPlacedGroup/FileInsideBadPlacedGroup.swift') in target.source_files)
    
    def test_xc_project_parser__gives_intentdefinition_as_source_file(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleUI')

        self.assertTrue(target.source_files)
        self.assertTrue(XcFile('/SampleUI/MyIntents.intentdefinition') in target.source_files)

    def test_xc_project_parser__gives_localized_intentdefinition_as_source_file(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleUI')

        self.assertTrue(target.source_files)
        self.assertTrue(XcFile('/SampleUI/Base.lproj/LocalizedIntents.intentdefinition') in target.source_files)
        self.assertTrue(XcFile('/SampleUI/en.lproj/LocalizedIntents.strings') in target.source_files)
        self.assertTrue(XcFile('/SampleUI/fr.lproj/LocalizedIntents.strings') in target.source_files)

    def test_xc_project_parser__gives_resource_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

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
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleCore')

        self.assertTrue(target.header_files)
        self.assertTrue(XcFile('/SampleCore/SampleCore.h') in target.header_files)

    def test_xc_project_parser__gives_linked_files_for_each_target(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        target = xcode_project.target_with_name('SampleiOSApp')

        self.assertTrue(target.linked_files)
        self.assertTrue(XcFile('/SampleiOSApp/libTouchJSONUniversal.a') in target.linked_files)
        self.assertTrue(XcFile('/SampleiOSApp/libTouchJSONUniversal2.a') in target.linked_files)

    # groups

    def test_xc_project_parser__gives_root_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project

        groups = xcode_project.groups

        self.assertTrue(XcGroup('/SampleCore', '/SampleCore') in groups)
        self.assertTrue(XcGroup('/SampleCoreTests', '/SampleCoreTests') in groups)
        self.assertTrue(XcGroup('/SampleUI', '/SampleUI') in groups)
        self.assertTrue(XcGroup('/SampleiOSApp', '/SampleiOSApp') in groups)
    
    def test_xc_project_parser__gives_children_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project
        
        group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]

        self.assertTrue(XcGroup('/SampleCore/RelativeToProject', '/SampleCore/RelativeToProject') in group.groups)
        self.assertTrue(XcGroup('/SampleCore/RelativeToProjectWithoutFolder', '/SampleCore/RelativeToProjectWithoutFolder') in group.groups)
        self.assertTrue(XcGroup('/SampleCore/Normal', '/SampleCore/Normal') in group.groups)
    
    def test_xc_project_parser__gives_grand_children_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project
        core_group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]

        group = [g for g in core_group.groups if g.group_path == '/SampleCore/Normal'][0]

        expected_group = XcGroup('/SampleCore/Normal/GrandChildGroup', '/SampleCore/Normal/GrandChildGroup')
        self.assertTrue(expected_group in group.groups)
    
    def test_xc_project_parser__gives_variant_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project
        app_group = [g for g in xcode_project.groups if g.group_path == '/SampleiOSApp'][0]

        self.assertTrue(XcGroup('/SampleiOSApp/Main.storyboard', '/SampleiOSApp/Main.storyboard') in app_group.groups)
    
    def test_xc_project_parser__set_project_relative_to_true__for_project_relative_group(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project
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
        xcode_project = project_parser.xc_project

        files = xcode_project.files

        self.assertTrue(XcFile('/README.md') in files)

    def test_xc_project_parser__gives_files_of_root_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project
        
        group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]

        self.assertTrue(XcFile('/SampleCore/SampleCore.swift') in group.files)
        self.assertTrue(XcFile('/SampleCore/GhostFolder/Ghost.swift') in group.files)
    
    def test_xc_project_parser__gives_files_of_other_groups(self):
        project_parser = self.fixture.sample_xc_project_parser
        xcode_project = project_parser.xc_project
        
        core_group = [g for g in xcode_project.groups if g.group_path == '/SampleCore'][0]
        bar_group = [g for g in core_group.groups if g.group_path == '/SampleCore/RelativeToProject'][0]
        foo_group = [g for g in core_group.groups if g.group_path == '/SampleCore/RelativeToProjectWithoutFolder'][0]

        self.assertTrue(XcFile('/SampleCore/RelativeToProject/InsideRelativeToProject.swift') in bar_group.files)
        self.assertTrue(XcFile('/SampleCore/InsideRelativeToProjectWithoutFolder.swift') in foo_group.files)


class SwiftCodeParserTests(TestCase):
    
    fixture = SwiftCodeParserFixture()

    # swift_types - accessibility

    def test__swift_types__gives_accessibility_internal__when_undefined(self):
        swift_code = "class MyClass \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.accessibility, "internal")

    def test__swift_types__gives_accessibility_public__when_public(self):
        swift_code = "public class MyClass \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.accessibility, "public")

    def test__swift_types__gives_accessibility_internal__when_internal(self):
        swift_code = "internal class MyClass \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.accessibility, "internal")

    def test__swift_types__gives_accessibility_fileprivate__when_fileprivate(self):
        swift_code = "fileprivate class MyClass \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.accessibility, "fileprivate")

    def test__swift_types__gives_accessibility_private__when_private(self):
        swift_code = "private class MyClass \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.accessibility, "private")

    # swift_types - type

    def test__swift_types__gives_class_declarations(self):
        swift_code = "class MyClass \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.type_identifier, "class")
        self.assertEqual(swift_type.name, "MyClass")

    def test__swift_types__gives_struct_declarations(self):
        swift_code = "struct MyStruct \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.type_identifier, "struct")
        self.assertEqual(swift_type.name, "MyStruct")

    def test__swift_types__gives_enum_declarations(self):
        swift_code = "enum MyEnum \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.type_identifier, "enum")
        self.assertEqual(swift_type.name, "MyEnum")

    def test__swift_types__gives_protocol_declarations(self):
        swift_code = "protocol MyProtocol \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.type_identifier, "protocol")
        self.assertEqual(swift_type.name, "MyProtocol")

    def test__swift_types__gives_extension_declarations(self):
        swift_code = "extension MyExtension \{\}"
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        types = parser.swift_types

        self.assertEqual(len(types), 1)
        swift_type = types.pop()
        self.assertEqual(swift_type.type_identifier, "extension")
        self.assertEqual(swift_type.name, "MyExtension")
    
    # swift_types - several type declarations

    def test__swift_types__gives_every_declaration_of_types(self):
        # Given
        swift_code = """
            class MyClass \{
            \}

            struct MyStruct \{
            \}

            extension MyClass \{

            \}

            enum MyEnum \{

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        types = parser.swift_types

        # Then
        self.assertEqual(len(types), 4)
        self.assertTrue(SwiftType('class', 'MyClass', 'internal') in types)
        self.assertTrue(SwiftType('struct', 'MyStruct', 'internal') in types)
        self.assertTrue(SwiftType('extension', 'MyClass', 'internal', discriminant='_3') in types)
        self.assertTrue(SwiftType('enum', 'MyEnum', 'internal') in types)
    
    # swift_types - super type

    def test__swift_types__set_inherited_types__for_a_class__when_super_class(self):
        # Given
        swift_code = """
            class MyClass: SuperClass \{
            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        types = parser.swift_types
        my_class = types[0]

        # Then
        self.assertEqual(len(types), 1)
        self.assertEqual(len(my_class.inherited_types), 1)
        self.assertEqual(my_class.inherited_types, {'SuperClass'})

    def test__swift_types__set_inherited_types__for_a_class__when_several_class_and_protocol_conformances(self):
        # Given
        swift_code = """
            class MyClass: SuperClass, Protocol1, Protocol2 \{
            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        types = parser.swift_types
        my_class = types[0]

        # Then
        self.assertEqual(len(types), 1)
        self.assertEqual(len(my_class.inherited_types), 3)
        self.assertEqual(my_class.inherited_types, {'SuperClass', 'Protocol1', 'Protocol2'})

    # swift_types - inner types - inside class

    def test__swift_types__gives_inner_type_declarations__when_inside_class(self):
        # Given
        swift_code = """
            public class OuterClass \{

                public class MyClass \{\}

                public struct MyStruct \{\}

                public enum MyEnum \{\}

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        types = parser.swift_types

        # Then
        self.assertEqual(len(types), 1)
        self.assertTrue(SwiftType('class', 'OuterClass', 'public') in types, types)

        inner_types = types[0].inner_types
        self.assertTrue(SwiftType('class', 'OuterClass.MyClass', 'public') in inner_types)
        self.assertTrue(SwiftType('struct', 'OuterClass.MyStruct', 'public') in inner_types)
        self.assertTrue(SwiftType('enum', 'OuterClass.MyEnum', 'public') in inner_types)

    # swift_types - inner types - inside class - 2 inner level

    def test__swift_types__gives_inner_type_declarations__when_inside_class__recursively(self):
        # Given
        swift_code = """
            public class MyClass \{

                public class InnerClass \{

                    public class InnerInnerClass \{\}

                \}

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        types = parser.swift_types

        # Then
        self.assertEqual(len(types), 1)
        self.assertTrue(SwiftType('class', 'MyClass', 'public') in types)

        inner_types = types[0].inner_types
        self.assertEqual(len(inner_types), 1)
        self.assertTrue(SwiftType('class', 'MyClass.InnerClass', 'public') in inner_types)

        inner_inner_types = inner_types[0].inner_types
        self.assertEqual(len(inner_inner_types), 1)
        self.assertTrue(SwiftType('class', 'MyClass.InnerClass.InnerInnerClass', 'public') in inner_inner_types)

    # swift_types - inner types - inside struct

    def test__swift_types__gives_inner_type_declarations__when_inside_struct(self):
        # Given
        swift_code = """
            public struct OuterStruct \{

                public class MyClass \{\}

                public struct MyStruct \{\}

                public enum MyEnum \{\}

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        types = parser.swift_types

        # Then
        self.assertEqual(len(types), 1)
        self.assertTrue(SwiftType('struct', 'OuterStruct', 'public') in types, types)

        inner_types = types[0].inner_types
        self.assertTrue(SwiftType('class', 'OuterStruct.MyClass', 'public') in inner_types)
        self.assertTrue(SwiftType('struct', 'OuterStruct.MyStruct', 'public') in inner_types)
        self.assertTrue(SwiftType('enum', 'OuterStruct.MyEnum', 'public') in inner_types)
    
    # swift_types

    def test__swift_types__gives_discriminant(self):
        # Given
        swift_code = """
            public struct MyStruct {

            }
        """
        parser = self.fixture.any_swift_code_parser(swift_code, base_discriminant='my_discriminant', type_counter=0)

        # When
        types = parser.swift_types

        # Then
        self.assertEqual(len(types), 1)
        self.assertTrue(SwiftType('struct', 'MyStruct', 'public', discriminant='my_discriminant_1') in types, types)
        self.assertEqual(types[0].discriminant, 'my_discriminant_1')

    def test__swift_types__gives_different_discriminant__for_different_types(self):
        # Given
        swift_code = """
            public struct MyStruct1 {

            }

            public struct MyStruct2 {

            }
        """
        parser = self.fixture.any_swift_code_parser(swift_code, base_discriminant='my_discriminant', type_counter=0)

        # When
        types = parser.swift_types

        # Then
        self.assertEqual(len(types), 2)
        self.assertTrue(SwiftType('struct', 'MyStruct1', 'public', discriminant='my_discriminant_1') in types, types)
        self.assertTrue(SwiftType('struct', 'MyStruct2', 'public', discriminant='my_discriminant_2') in types, types)
        self.assertEqual(types[0].discriminant, 'my_discriminant_1')
        self.assertEqual(types[1].discriminant, 'my_discriminant_2')

    # used_types - member types

    def test__used_types__gives_types_of_members__for_a_class(self):
        # Given
        swift_code = """
            class MyClass \{
                let member: LetMember
                let optionalMember: OptionalLetMember?
                var member: VarMember
                var optionalMember: OptionalVarMember?
            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        used_types = parser.swift_types[0].used_types

        # Then
        self.assertEqual(len(used_types), 4)
        self.assertEqual(used_types, {'LetMember', 'OptionalLetMember', 'VarMember', 'OptionalVarMember'})

    def test__used_types__gives_types_of_members__for_a_struct(self):
        # Given
        swift_code = """
            struct MyStruct \{
                let member: LetMember
                let optionalMember: OptionalLetMember?
                var member: VarMember
                var optionalMember: OptionalVarMember?
            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        used_types = parser.swift_types[0].used_types

        # Then
        self.assertEqual(len(used_types), 4)
        self.assertEqual(used_types, {'LetMember', 'OptionalLetMember', 'VarMember', 'OptionalVarMember'})

    # used_types - method - parameters and return type

    def test__used_types__gives_return_type_of_method(self):
        swift_code = """
            class MyClass \{
                
                func myMethod() -> ReturnType \{
                \}

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        used_types = parser.swift_types[0].used_types

        # Then
        self.assertEqual(len(used_types), 1)
        self.assertEqual(used_types, {'ReturnType'})

    def test__used_types__gives_not_type_for_a_method__without_return_type(self):
        swift_code = """
            class MyClass \{
                
                func myMethod() \{
                \}

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        used_types = parser.swift_types[0].used_types

        # Then
        self.assertEqual(len(used_types), 0)

    def test__used_types__gives_types_of_method_parameters(self):
        swift_code = """
            class MyClass \{
                
                func myMethod(param1: Type1, param2: Type2) \{
                \}

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        used_types = parser.swift_types[0].used_types

        # Then
        self.assertEqual(len(used_types), 2)
        self.assertEqual(used_types, {'Type1', 'Type2'})

    def test__used_types__gives_types_of_method_parameters__and_return_type(self):
        swift_code = """
            class MyClass \{
                
                func myMethod(param1: Type1, param2: Type2) -> ReturnType \{
                \}

            \}
        """
        parser = self.fixture.any_swift_code_parser(swift_code)
        
        # When
        used_types = parser.swift_types[0].used_types

        # Then
        self.assertEqual(len(used_types), 3)
        self.assertEqual(used_types, {'Type1', 'Type2', 'ReturnType'})
