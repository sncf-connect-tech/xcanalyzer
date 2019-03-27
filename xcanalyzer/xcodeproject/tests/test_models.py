from unittest import TestCase

from ..models import XcTarget, XcProject, XcGroup, XcFile

from .fixtures import XcModelsFixture


class XcFileTests(TestCase):

    # __init__

    def test_init_xc_file(self):
        xc_file = XcFile(name='MyFile', path='/MyFile')

        self.assertTrue(xc_file)
        self.assertEqual(xc_file.name, 'MyFile')

    # __eq__

    def test_xc_files_are_not_equal__when_different_name(self):
        file_1 = XcFile(name="MyFile1", path='/MyFile1')
        file_2 = XcFile(name="MyFile2", path='/MyFile2')

        self.assertFalse(file_1 == file_2)

    def test_xc_files_are_equal__when_same_name(self):
        file_1 = XcFile(name="MyFile", path='/MyFile')
        file_2 = XcFile(name="MyFile", path='/MyFile')

        self.assertTrue(file_1 == file_2)

    # __hash__

    def test_xc_file_hashes_are_same__when_same_name(self):
        file_1 = XcFile(name="MyFile", path='/MyFile')
        file_2 = XcFile(name="MyFile", path='/MyFile')

        hash_1 = hash(file_1)
        hash_2 = hash(file_2)

        self.assertEqual(hash_1, hash_2)
    
    # __repr__

    def test_xc_file_repr_contain_name(self):
        xc_file = XcFile(name="MyFile", path='/MyFile')

        representation = str(xc_file)

        self.assertEqual(representation, "<XcFile> MyFile")


class XcGroupTests(TestCase):

    fixture = XcModelsFixture()

    # __init__

    def test_init_xc_group(self):
        xc_group = XcGroup(name='MyGroup')

        self.assertTrue(xc_group)
        self.assertEqual(xc_group.name, 'MyGroup')
    
    def test_init_xc_group__with_groups__has_groups(self):
        group = self.fixture.any_group()
        groups = set([group])

        xc_group = XcGroup(name='MyGroup', groups=groups)

        self.assertEqual(xc_group.groups, groups)
    
    def test_init_xc_group__with_groups__has_groups(self):
        my_file = self.fixture.any_file()
        files = set([my_file])

        xc_group = XcGroup(name='MyGroup', files=files)

        self.assertEqual(xc_group.files, files)
    
    # __eq__

    def test_xc_groups_are_not_equal__when_different_name(self):
        group_1 = XcGroup(name="MyGroup1")
        group_2 = XcGroup(name="MyGroup2")

        self.assertFalse(group_1 == group_2)

    def test_xc_groups_are_equal__when_same_name(self):
        group_1 = XcGroup(name="MyGroup")
        group_2 = XcGroup(name="MyGroup")

        self.assertTrue(group_1 == group_2)

    # __hash__

    def test_xc_group_hashes_are_same__when_same_name(self):
        group_1 = XcGroup(name="MyGroup")
        group_2 = XcGroup(name="MyGroup")

        hash_1 = hash(group_1)
        hash_2 = hash(group_2)

        self.assertEqual(hash_1, hash_2)
    
    # __repr__

    def test_xc_group_repr_contain_name(self):
        group = XcGroup(name="MyGroup")

        representation = str(group)

        self.assertEqual(representation, "<XcGroup> MyGroup")
    

class XcProjectTests(TestCase):

    fixture = XcModelsFixture()

    # __init__

    def test_instantiate_xc_project(self):
        xc_project = XcProject(name="MyXcProject", targets=set(), groups=set(), files=set())

        self.assertTrue(xc_project)
        self.assertEqual(xc_project.name, "MyXcProject")

    def test_instantiate_xc_project__with_targets__has_targets(self):
        target = self.fixture.any_target()
        targets = set([target])
        
        xc_project = XcProject(name="MyXcProject", targets=targets, groups=set(), files=set())

        self.assertEqual(xc_project.targets, targets)

    def test_instantiate_xc_project__with_groups__has_groups(self):
        group = self.fixture.any_group()
        groups = set([group])
        
        xc_project = XcProject(name="MyXcProject", targets=set(), groups=groups, files=set())

        self.assertEqual(xc_project.groups, groups)

    # targets_of_type

    def test_targets_of_type__returns_filtered_target_by_type(self):
        target_1 = self.fixture.any_target(target_type=XcTarget.Type.UI_TEST)
        target_2 = self.fixture.any_target(target_type=XcTarget.Type.TEST)
        target_3 = self.fixture.any_target(target_type=XcTarget.Type.APPLICATION)
        targets = set([target_1, target_2, target_3])
        xc_project = XcProject(name="MyXcProject", targets=targets, groups=set(), files=set())

        targets = xc_project.targets_of_type(XcTarget.Type.UI_TEST)

        self.assertEqual(targets, [target_1])
    
    # target_with_name

    def test_target_with_name__returns_none__when_no_matching_target_name(self):
        target_1 = self.fixture.any_target(name='MyTarget1')
        xc_project = XcProject(name="MyXcProject", targets=set([target_1]), groups=set(), files=set())

        target_2 = xc_project.target_with_name('MyTarget2')

        self.assertIsNone(target_2)

    def test_target_with_name__returns_target__when_a_target_name_matches(self):
        target = self.fixture.any_target(name='MyTarget')
        xc_project = XcProject(name="MyXcProject", targets=set([target]), groups=set(), files=set())

        resulting_target = xc_project.target_with_name('MyTarget')

        self.assertEqual(resulting_target, target)

    # group_paths
    def test_group_paths__gives_correct_sorted_paths_list(self):
        group_C = XcGroup(name="MyGroupC")
        group_B = XcGroup(name="MyGroupB", groups = set([group_C]))
        group_A = XcGroup(name="MyGroupA", groups = set([group_B]))

        project = XcProject(name="MyProject", targets=set(), groups=set([group_A]), files=set())

        expected_paths = [
            '/MyGroupA',
            '/MyGroupA/MyGroupB',
            '/MyGroupA/MyGroupB/MyGroupC',
        ]
        self.assertEqual(expected_paths, project.group_paths)


class XcTargetTests(TestCase):

    fixture = XcModelsFixture()

    # __init__

    def test_instantiate_xc_target(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        self.assertTrue(xc_target)
        self.assertEqual(xc_target.name, "MyXcTarget")

    def test_instantiate_xc_target__without_dependencies__has_no_dependency(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        self.assertFalse(xc_target.dependencies)
    
    def test_instantiate_xc_target__with_dependencies__has_dependencies(self):
        target_dep = self.fixture.any_target(name='MyDep')

        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, dependencies=set([target_dep]))

        self.assertTrue(target_dep in xc_target.dependencies)
    
    def test_instantiate_xc_target__without__source_files_has_no_source_file(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        self.assertFalse(xc_target.source_files)

    def test_instantiate_xc_target__with_source_files__has_source_files(self):
        any_file = '/path/to/my/file'

        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, source_files=set([any_file]))

        self.assertTrue(any_file in xc_target.source_files)
    
    def test_instantiate_xc_target__without__resource_files_has_no_resource_file(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        self.assertFalse(xc_target.resource_files)

    def test_instantiate_xc_target__with_resource_files__has_resource_files(self):
        any_file = '/path/to/my/file'

        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST, resource_files=set([any_file]))

        self.assertTrue(any_file in xc_target.resource_files)
    
    # __eq__

    def test_xc_targets_are_not_equal__when_different_type(self):
        xc_target_1 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)
        xc_target_2 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.TEST)

        self.assertFalse(xc_target_1 == xc_target_2)

    def test_xc_targets_are_not_equal__when_different_name(self):
        xc_target_1 = XcTarget(name="MyXcTarget1", target_type=XcTarget.Type.UI_TEST)
        xc_target_2 = XcTarget(name="MyXcTarget2", target_type=XcTarget.Type.UI_TEST)

        self.assertFalse(xc_target_1 == xc_target_2)
    
    def test_xc_targets_are_equal__when_same_name_and_type(self):
        xc_target_1 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)
        xc_target_2 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        self.assertTrue(xc_target_1 == xc_target_2)
    
    # __hash__

    def test_xc_targets_hashes_are_same__when_same_type_and_name(self):
        xc_target_1 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)
        xc_target_2 = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        hash_1 = hash(xc_target_1)
        hash_2 = hash(xc_target_2)

        self.assertEqual(hash_1, hash_2)
    
    # __repr__

    def test_xc_target_repr_contain_name(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        representation = str(xc_target)

        self.assertEqual(representation, "<XcTarget> MyXcTarget")