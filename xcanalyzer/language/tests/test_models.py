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