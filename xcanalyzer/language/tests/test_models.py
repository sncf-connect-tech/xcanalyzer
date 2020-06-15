from unittest import TestCase

from ..models import SwiftType

class SwiftTypeTests(TestCase):

    # inherits_from_view_controller

    def test__inherits_from_view_controller__returns_false__when_not_a_class(self):
        struct = SwiftType('struct', 'MyStruct', 'internal')
        enum = SwiftType('enum', 'MyEnum', 'internal')
        protocol = SwiftType('protocol', 'MyProtocol', 'internal')
        extension = SwiftType('extension', 'UIViewController', 'internal')

        self.assertEqual(struct.inherits_from_view_controller, False)
        self.assertEqual(enum.inherits_from_view_controller, False)
        self.assertEqual(protocol.inherits_from_view_controller, False)
        self.assertEqual(extension.inherits_from_view_controller, False)

    def test__inherits_from_view_controller__returns_false__when_class_not_inheriting_ui_view_controller(self):
        my_class_1 = SwiftType('class', 'MyClass', 'internal', raw_inherited_types=set())
        my_class_2 = SwiftType('class', 'MyClass', 'internal', raw_inherited_types={'OtherThanUIViewController'})

        self.assertEqual(my_class_1.inherits_from_view_controller, False)
        self.assertEqual(my_class_2.inherits_from_view_controller, False)

    def test__inherits_from_view_controller__returns_true__when_class_inherits_ui_view_controller(self):
        my_class_1 = SwiftType('class', 'MyClass', 'internal', raw_inherited_types={'UIViewController'})
        my_class_2 = SwiftType('class', 'MyClass', 'internal', raw_inherited_types={'UINavigationController'})
        my_class_3 = SwiftType('class', 'MyClass', 'internal', raw_inherited_types={'UITabBarController'})

        self.assertEqual(my_class_1.inherits_from_view_controller, True)
        self.assertEqual(my_class_2.inherits_from_view_controller, True)
        self.assertEqual(my_class_3.inherits_from_view_controller, True)

    def test__inherits_from_view_controller__returns_true__when_class_inherits_ui_view_controller__and_other_protocol(self):
        my_class = SwiftType('class', 'MyClass', 'internal', raw_inherited_types={'UIViewController', 'Protocol1', 'Procotol2'})
        
        self.assertEqual(my_class.inherits_from_view_controller, True)

    def test__inherits_from_view_controller__returns_true_when_class_inherits__from_generic_ui_view_controller(self):
        my_class = SwiftType('class', 'MyClass', 'internal', raw_inherited_types={'UIViewController<Bool>'})

        self.assertEqual(my_class.inherits_from_view_controller, True)
    
    # __eq__

    def test__eq__returns_false__when_different_type_identifiers(self):
        type_1 = SwiftType('class', 'MyType', 'internal')
        type_2 = SwiftType('struct', 'MyType', 'internal')

        self.assertEqual(type_1 == type_2, False)

    def test__eq__returns_false__when_different_names(self):
        type_1 = SwiftType('class', 'MyType1', 'internal')
        type_2 = SwiftType('class', 'MyType2', 'internal')

        self.assertEqual(type_1 == type_2, False)

    def test__eq__returns_false__when_different_fullnames(self):
        type_0 = SwiftType('class', 'MyParentType', 'internal')
        type_1 = SwiftType('class', 'MyType', 'internal')
        type_2 = SwiftType('class', 'MyType', 'internal')
        type_1.parent_type = type_0

        self.assertEqual(type_1 == type_2, False)

    def test__eq__returns_false__when_different_accessibility(self):
        type_1 = SwiftType('class', 'MyType', 'internal')
        type_2 = SwiftType('class', 'MyType', 'public')

        self.assertEqual(type_1 == type_2, False)

    def test__eq__returns_true__when_same_type_identifier__and_same_fullname__and_same_accessibility(self):
        type_1 = SwiftType('class', 'MyType', 'internal')
        type_2 = SwiftType('class', 'MyType', 'internal')

        self.assertEqual(type_1 == type_2, True)

    # __eq__ - discriminant

    def test__eq__returns_false__for_extensions__with_different_discriminant(self):
        type_1 = SwiftType('extension', 'MyType', 'internal',
                           discriminant='extension_1')
        type_2 = SwiftType('extension', 'MyType', 'internal', 
                           discriminant='extension_2')
        
        self.assertEqual(type_1 == type_2, False)

    def test__eq__returns_true__for_extensions__with_same_discriminant(self):
        type_1 = SwiftType('extension', 'MyType', 'internal',
                           discriminant='extension_disc')
        type_2 = SwiftType('extension', 'MyType', 'internal', 
                           discriminant='extension_disc')
        
        self.assertEqual(type_1 == type_2, True)

    def test__eq__returns_true__for_non_extensions__with_different_discriminant(self):
        type_1 = SwiftType('class', 'MyType', 'internal',
                           discriminant='extension_1')
        type_2 = SwiftType('class', 'MyType', 'internal', 
                           discriminant='extension_2')
        
        self.assertEqual(type_1 == type_2, True)
