from unittest import TestCase

from ..models import XcTarget, XcProject, XcGroup, XcFile

from .fixtures import XcModelsFixture


class XcFileTests(TestCase):

    # __init__

    def test_init_xc_file(self):
        xc_file = XcFile(filepath='/MyFile')

        self.assertTrue(xc_file)
        self.assertEqual(xc_file.filepath, '/MyFile')

    # __eq__

    def test_xc_files_are_not_equal__when_different_filepath(self):
        file_1 = XcFile(filepath='/MyFile1')
        file_2 = XcFile(filepath='/MyFile2')

        self.assertFalse(file_1 == file_2)

    def test_xc_files_are_equal__when_same_filepath(self):
        file_1 = XcFile(filepath='/MyFile')
        file_2 = XcFile(filepath='/MyFile')

        self.assertTrue(file_1 == file_2)

    # __hash__

    def test_xc_file_hashes_are_same__when_same_filepath(self):
        file_1 = XcFile(filepath='/MyFile')
        file_2 = XcFile(filepath='/MyFile')

        hash_1 = hash(file_1)
        hash_2 = hash(file_2)

        self.assertEqual(hash_1, hash_2)
    
    # __repr__

    def test_xc_file_repr_contains_filepath(self):
        xc_file = XcFile(filepath='/MyFile')

        representation = str(xc_file)

        self.assertEqual(representation, "<XcFile> /MyFile")
    

class XcGroupTests(TestCase):

    fixture = XcModelsFixture()

    # __init__

    def test_init_xc_group(self):
        xc_group = XcGroup(group_path='/MyGroup', filepath='/MyGroup')

        self.assertTrue(xc_group)
        self.assertEqual(xc_group.group_path, '/MyGroup')
    
    def test_init_xc_group__with_groups__has_groups(self):
        group = self.fixture.any_group()
        groups = set([group])

        xc_group = XcGroup(group_path='/MyGroup', filepath='/MyGroup', groups=groups)

        self.assertEqual(xc_group.groups, groups)
    
    def test_init_xc_group__with_groups__has_groups(self):
        my_file = self.fixture.any_file()
        files = set([my_file])

        xc_group = XcGroup(group_path='/MyGroup', filepath='/MyGroup', files=files)

        self.assertEqual(xc_group.files, files)
    
    # __eq__

    def test_xc_groups_are_not_equal__when_different_group_path(self):
        group_1 = XcGroup(group_path="/MyGroup1", filepath="/MyGroup")
        group_2 = XcGroup(group_path="/MyGroup2", filepath="/MyGroup")

        self.assertFalse(group_1 == group_2)

    def test_xc_groups_are_equal__when_same_group_path(self):
        group_1 = XcGroup(group_path="/MyGroup", filepath="/MyGroup1")
        group_2 = XcGroup(group_path="/MyGroup", filepath="/MyGroup2")

        self.assertTrue(group_1 == group_2)

    # __hash__

    def test_xc_group_hashes_are_same__when_same_group_path(self):
        group_1 = XcGroup(group_path="/MyGroup", filepath="/MyGroup1")
        group_2 = XcGroup(group_path="/MyGroup", filepath="/MyGroup2")

        hash_1 = hash(group_1)
        hash_2 = hash(group_2)

        self.assertEqual(hash_1, hash_2)
    
    # __repr__

    def test_xc_group_repr_contains_group_path(self):
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroupFilePath")

        representation = str(group)

        self.assertEqual(representation, "<XcGroup> /MyGroup [/MyGroupFilePath]")
    
    # has_folder

    def test_xc_group_has_folder__returns_true__when_same_group_path_and_filepath(self):
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroup")

        has_folder = group.has_folder

        self.assertEqual(has_folder, True)

    def test_xc_group_has_folder__returns_false__when_different_group_path_and_filepath(self):
        group = XcGroup(group_path="/MyGroup", filepath="/OtherGroup")

        has_folder = group.has_folder

        self.assertEqual(has_folder, False)
    

class XcProjectTests(TestCase):

    fixture = XcModelsFixture()

    # __init__

    def test_instantiate_xc_project(self):
        xc_project = XcProject(dirpath='/', name="MyXcProject", targets=set(), groups=set(), files=set())

        self.assertTrue(xc_project)
        self.assertEqual(xc_project.dirpath, '/')
        self.assertEqual(xc_project.name, "MyXcProject")

    def test_instantiate_xc_project__with_targets__has_targets(self):
        target = self.fixture.any_target()
        targets = set([target])
        
        xc_project = XcProject(dirpath='/', name="MyXcProject", targets=targets, groups=set(), files=set())

        self.assertEqual(xc_project.targets, targets)

    def test_instantiate_xc_project__with_groups__has_groups(self):
        group = self.fixture.any_group()
        groups = set([group])
        
        xc_project = XcProject(dirpath='/', name="MyXcProject", targets=set(), groups=groups, files=set())

        self.assertEqual(xc_project.groups, groups)

    # targets_of_type

    def test_targets_of_type__returns_filtered_target_by_type(self):
        target_1 = self.fixture.any_target(target_type=XcTarget.Type.UI_TEST)
        target_2 = self.fixture.any_target(target_type=XcTarget.Type.TEST)
        target_3 = self.fixture.any_target(target_type=XcTarget.Type.APPLICATION)
        targets = set([target_1, target_2, target_3])
        xc_project = XcProject(dirpath='/', name="MyXcProject", targets=targets, groups=set(), files=set())

        targets = xc_project.targets_of_type(XcTarget.Type.UI_TEST)

        self.assertEqual(targets, [target_1])
    
    # target_with_name

    def test_target_with_name__returns_none__when_no_matching_target_name(self):
        target_1 = self.fixture.any_target(name='MyTarget1')
        xc_project = XcProject(dirpath='/', name="MyXcProject", targets=set([target_1]), groups=set(), files=set())

        target_2 = xc_project.target_with_name('MyTarget2')

        self.assertIsNone(target_2)

    def test_target_with_name__returns_target__when_a_target_name_matches(self):
        target = self.fixture.any_target(name='MyTarget')
        xc_project = XcProject(dirpath='/', name="MyXcProject", targets=set([target]), groups=set(), files=set())

        resulting_target = xc_project.target_with_name('MyTarget')

        self.assertEqual(resulting_target, target)

    # groups_filtered - all

    def test_groups_filtered__gives_all_paths__sorted(self):
        group_C = XcGroup(group_path="/MyGroupA/MyGroupB/MyGroupC", filepath="/MyGroupA/MyGroupB/MyGroupC")
        group_B = XcGroup(group_path="/MyGroupA/MyGroupB", filepath="/MyGroupA/MyGroupB", groups=set([group_C]))
        group_A = XcGroup(group_path="/MyGroupA", filepath="/MyGroupA", groups=set([group_B]))
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=set([group_A]), files=set())

        groups = project.groups_filtered()

        expected_paths = [
            '/MyGroupA',
            '/MyGroupA/MyGroupB',
            '/MyGroupA/MyGroupB/MyGroupC',
        ]
        paths = [g.group_path for g in groups]
        self.assertEqual(paths, expected_paths)
    
    # groups_filtered - empty
    
    def test_groups_filtered__gives_empty_groups__when_filter_empty(self):
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroup")
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=set([group]), files=set())

        groups = project.groups_filtered(filter_mode='empty')

        paths = [g.group_path for g in groups]
        self.assertEqual(paths, ['/MyGroup'])
    
    def test_groups_filtered__exclude_groups_with_files__when_filter_empty(self):
        file = self.fixture.any_file()
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroup", files=set([file]))
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=set([group]), files=set())

        groups = project.groups_filtered(filter_mode='empty')

        self.assertFalse(groups)

    def test_groups_filtered__exclude_groups_with_groups__when_filter_empty(self):
        subgroup = XcGroup(group_path="/MyGroup/MySubGroup", filepath="/MyGroup/MySubGroup")
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroup", groups=set([subgroup]))
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=set([group]), files=set())

        groups = project.groups_filtered(filter_mode='empty')

        paths = [g.group_path for g in groups]
        self.assertFalse('/MyGroup' in paths)
    
    # groups_filtered - project_relative

    def test_groups_filtered__gives_project_relative_groups__when_filter_project_relative(self):
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroup", is_project_relative=True)
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=set([group]), files=set())

        groups = project.groups_filtered(filter_mode='project_relative')
        
        self.assertEqual(len(groups), 1)
        paths = [g.group_path for g in groups]
        self.assertTrue('/MyGroup' in paths)
    
    def test_groups_filtered__exclude_groups_non_project_relative__when_filter_project_relative(self):
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroup", is_project_relative=False)
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=set([group]), files=set())

        groups = project.groups_filtered(filter_mode='project_relative')

        self.assertFalse(groups)
    
    # groups_filtered - without_folder

    def test_groups_filtered__gives_groups_without_folder__when_filter_without_folder(self):
        group_relative_group = XcGroup(group_path="/Parent/Group1", filepath="/Parent", is_project_relative=False)
        project_relative_group = XcGroup(group_path="/Parent/Group2", filepath="/Parent", is_project_relative=True)
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=[group_relative_group, project_relative_group], files=set())

        groups = project.groups_filtered(filter_mode='without_folder')

        self.assertEqual(len(groups), 2)
    
    def test_groups_filtered__excludes_groups_with_folder__when_filter_without_folder(self):
        group_relative_group = XcGroup(group_path="/Parent/Group1", filepath="/Parent/Group1", is_project_relative=False)
        project_relative_group = XcGroup(group_path="/Parent/Group2", filepath="/Parent/Group2", is_project_relative=True)
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=[group_relative_group, project_relative_group], files=set())

        groups = project.groups_filtered(filter_mode='without_folder')

        self.assertFalse(groups)
    
    def test_groups_filtered__excludes_variant_groups__when_filter_without_folder(self):
        variant_group = XcGroup(group_path="/VariantGroup", filepath="/", is_variant=True)
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=[variant_group], files=set())

        groups = project.groups_filtered(filter_mode='without_folder')

        self.assertFalse(groups)
    
    # groups_filtered - variant
    
    def test_groups_filtered__gives_variant_groups__when_filter_variant(self):
        variant_group = XcGroup(group_path="/MyGroup", filepath="/MyGroup", is_variant=True)
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=[variant_group], files=set())

        groups = project.groups_filtered(filter_mode='variant')

        self.assertTrue(groups)
    
    def test_groups_filtered__excludes_non_variant_groups__when_filter_variant(self):
        group = XcGroup(group_path="/MyGroup", filepath="/MyGroup", is_variant=False)
        project = XcProject(dirpath='/', name="MyProject", targets=set(), groups=[group], files=set())

        groups = project.groups_filtered(filter_mode='variant')

        self.assertFalse(groups)
    
    # target_files

    def test_target_files(self):
        # Given
        file_1 = XcFile('/MyFile1')
        target_1 = self.fixture.any_target(name='MyTarget1', resource_files=set([file_1]))

        file_2 = XcFile('/MyFile2')
        target_2 = self.fixture.any_target(name='MyTarget2', resource_files=set([file_2]))

        project = XcProject(dirpath='/', name="MyProject", targets=set([target_1, target_2]), groups=[], files=set())

        # When
        target_files = project.target_files

        # Then
        self.assertEqual(len(target_files), 2)
        self.assertTrue(file_1 in target_files)
        self.assertTrue(file_2 in target_files)


class XcTargetTests(TestCase):

    fixture = XcModelsFixture()

    # __init__

    def test_instantiate_xc_target(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        self.assertTrue(xc_target)
        self.assertEqual(xc_target.name, "MyXcTarget")
        self.assertEqual(xc_target.product_name, "MyProduct")

    def test_instantiate_xc_target__without_dependencies__has_no_dependency(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        self.assertFalse(xc_target.dependencies)
    
    # __init__ - dependencies

    def test_instantiate_xc_target__with_dependencies__has_dependencies(self):
        target_dep = self.fixture.any_target(name='MyDep')

        xc_target = XcTarget(name="MyXcTarget",
                             target_type=XcTarget.Type.UI_TEST,
                             product_name='MyProduct',
                             dependencies=set([target_dep]))

        self.assertTrue(target_dep in xc_target.dependencies)
    
    # __init__ - linked_frameworks

    def test_instantiate_xc_target__with_linked_frameworks__has_linked_frameworks(self):
        linked_framework = self.fixture.any_target(name='MyFmk')

        xc_target = XcTarget(name="MyXcTarget",
                             target_type=XcTarget.Type.FRAMEWORK,
                             product_name='MyProduct',
                             linked_frameworks=set([linked_framework]))
        
        self.assertTrue(linked_framework in xc_target.linked_frameworks)

    # __init__ - embed_frameworks

    def test_instantiate_xc_target__with_linked_frameworks__has_embed_frameworks(self):
        embed_framework = self.fixture.any_target(name='MyFmk')

        xc_target = XcTarget(name="MyXcTarget",
                             target_type=XcTarget.Type.FRAMEWORK,
                             product_name='MyProduct',
                             embed_frameworks=set([embed_framework]))
        
        self.assertTrue(embed_framework in xc_target.embed_frameworks)

    # __init__ - source files

    def test_instantiate_xc_target__without__source_files_has_no_source_file(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        self.assertFalse(xc_target.source_files)

    def test_instantiate_xc_target__with_source_files__has_source_files(self):
        any_file = self.fixture.any_file()

        xc_target = XcTarget(name="MyXcTarget",
                             target_type=XcTarget.Type.UI_TEST,
                             product_name='MyProduct',
                             source_files=set([any_file]))

        self.assertTrue(any_file in xc_target.source_files)
    
    # __init__ - resource files

    def test_instantiate_xc_target__without__resource_files_has_no_resource_file(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        self.assertFalse(xc_target.resource_files)

    def test_instantiate_xc_target__with_resource_files__has_resource_files(self):
        any_file = self.fixture.any_file()

        xc_target = XcTarget(name="MyXcTarget",
                             target_type=XcTarget.Type.UI_TEST,
                             product_name='MyProduct',
                             resource_files=set([any_file]))

        self.assertTrue(any_file in xc_target.resource_files)
    
    # __init__ - header files

    def test_instantiate_xc_target__with_header_files__has_header_files(self):
        any_file = self.fixture.any_file()

        xc_target = XcTarget(name="MyXcTarget",
                             target_type=XcTarget.Type.UI_TEST,
                             product_name='MyProduct',
                             header_files=set([any_file]))

        self.assertTrue(any_file in xc_target.header_files)

    def test_instantiate_xc_target__without__header_files_has_no_header_file(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        self.assertFalse(xc_target.header_files)

    # __eq__

    def test_xc_targets_are_not_equal__when_different_type(self):
        xc_target_1 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')
        xc_target_2 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.TEST, product_name='MyProduct')

        self.assertFalse(xc_target_1 == xc_target_2)

    def test_xc_targets_are_not_equal__when_different_name(self):
        xc_target_1 = XcTarget(name="MyXcTarget1", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')
        xc_target_2 = XcTarget(name="MyXcTarget2", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        self.assertFalse(xc_target_1 == xc_target_2)
    
    def test_xc_targets_are_equal__when_same_name_and_type(self):
        xc_target_1 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')
        xc_target_2 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        self.assertTrue(xc_target_1 == xc_target_2)
    
    # __hash__

    def test_xc_targets_hashes_are_same__when_same_type_and_name(self):
        xc_target_1 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')
        xc_target_2 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        hash_1 = hash(xc_target_1)
        hash_2 = hash(xc_target_2)

        self.assertEqual(hash_1, hash_2)
    
    # __repr__

    def test_xc_target_repr_contain_name(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, product_name='MyProduct')

        representation = str(xc_target)

        self.assertEqual(representation, "<XcTarget> MyXcTarget")
    
    # files

    def test_files_gives_source_resource_and_header_files(self):
        source_file = XcFile('/SourceFile')
        resource_file = XcFile('/ResourceFile')
        header_file = XcFile('/HeaderFile')
        xc_target = XcTarget(name="MyXcTarget",
                        target_type=XcTarget.Type.UI_TEST,
                        product_name='MyProduct',
                        source_files=set([source_file]),
                        resource_files=set([resource_file]),
                        header_files=set([header_file]))
        
        files = xc_target.files
        
        expected_files = set([source_file, resource_file, header_file])
        self.assertEqual(expected_files, files)
