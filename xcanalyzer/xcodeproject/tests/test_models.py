from unittest import TestCase

from ..models import XcTarget, XcProject

from .fixtures import XcModelsFixture


class XcProjectTests(TestCase):

    fixture = XcModelsFixture()

    # __init__

    def test_instantiate_xc_project(self):
        xc_project = XcProject(name="MyXcProject", targets=set())

        self.assertTrue(xc_project)
        self.assertEqual(xc_project.name, "MyXcProject")

    def test_instantiate_xc_project__with_targets__has_targets(self):
        target = self.fixture.any_target()
        targets = set([target])
        
        xc_project = XcProject(name="MyXcProject", targets=targets)

        self.assertEqual(xc_project.targets, targets)
    
    # targets_of_type

    def test_targets_of_type__returns_filtered_target_by_type(self):
        target_1 = self.fixture.any_target(target_type=XcTarget.Type.UI_TEST)
        target_2 = self.fixture.any_target(target_type=XcTarget.Type.TEST)
        target_3 = self.fixture.any_target(target_type=XcTarget.Type.APPLICATION)
        targets = set([target_1, target_2, target_3])
        xc_project = XcProject(name="MyXcProject", targets=targets)

        targets = xc_project.targets_of_type(XcTarget.Type.UI_TEST)

        self.assertEqual(targets, set([target_1]))


class XcTargetTests(TestCase):

    # __init__

    def test_instantiate_xc_target(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        self.assertTrue(xc_target)
        self.assertEqual(xc_target.name, "MyXcTarget")

    def test_instantiate_xc_target__without_dependencies__has_no_dependency(self):
        xc_target = XcTarget(name="MyXcTarget", target_type=XcTarget.Type.UI_TEST)

        self.assertFalse(xc_target.dependencies)
    
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