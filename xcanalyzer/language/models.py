UI_VIEW_CONTROLLER_BASE_CLASSES = {
    'UIViewController',
    'UINavigationController',
    'UISplitViewController',
    'UITabBarController',
}

class SwiftAccessibility():

    PRIVATE = 'private'
    FILEPRIVATE = 'fileprivate'
    INTERNAL = 'internal'
    PUBLIC = 'public'
    OPEN = 'open'

    ALL = {
        PRIVATE,
        FILEPRIVATE,
        INTERNAL,
        PUBLIC,
        OPEN,
    }


class SwiftExtensionScope():

    FILE = 'file'  # extensions of Swift types defined in the same file
    PROJECT_SWIFT = 'project_swift'  # extensions of Swift types defined in the project
    PROJECT_OBJC = 'project_objc'  # extensions of Objective-C types defined in the project
    OUTER = 'outer'  # iOS SDK and third-party libraries

    ALL = {
        FILE,
        PROJECT_SWIFT,
        PROJECT_OBJC,
        OUTER,
    }


class SwiftTypeType():

    PROTOCOL = 'protocol'
    EXTENSION = 'extension'
    STRUCT = 'struct'
    ENUM = 'enum'
    CLASS = 'class'

    ALL = {
        PROTOCOL,
        EXTENSION,
        STRUCT,
        ENUM,
        CLASS,
    }


class SwiftType():

    def __init__(self, type_identifier, name, accessibility, raw_inherited_types=set(), discriminant=None):
        assert type_identifier in SwiftTypeType.ALL
        assert accessibility in SwiftAccessibility.ALL

        self.type_identifier = type_identifier
        self.name = name
        self.accessibility = accessibility
        self.raw_inherited_types = raw_inherited_types
        self.discriminant = discriminant

        self.parent_type = None
        self.inner_types = list()

        self.used_types = set()

        self.file = None
    
    def __repr__(self):
        return '{:<11} {:<9} {}'.format(self.accessibility, self.type_identifier, self.name)
    
    def __eq__(self, other):
        return self.type_identifier == other.type_identifier and \
            self.fullname == other.fullname and \
            self.accessibility == other.accessibility and \
            (self.type_identifier != SwiftTypeType.EXTENSION or self.discriminant == other.discriminant)
    
    def __hash__(self):
        return hash((self.type_identifier, self.name, self.accessibility))

    @property
    def fullname(self):
        names = [self.name]

        parent = self.parent_type
        while parent:
            names.append(parent.name)
            parent = parent.parent_type
        
        return '.'.join(reversed(names))

    @property
    def inherited_types(self):
        results = set()
        
        for raw_inherited_type in self.raw_inherited_types:
            if '<' in raw_inherited_type:
                inherited_type = raw_inherited_type[:raw_inherited_type.index('<')]
                results.add(inherited_type)
            else:
                results.add(raw_inherited_type)

        return results

    @property
    def inherits_from_view_controller(self):
        return bool(UI_VIEW_CONTROLLER_BASE_CLASSES & self.inherited_types)
    
    def inherits_from_one_of(self, class_names):
        return bool(class_names & self.inherited_types)
    
    def inner_types_all_filtered(self, type_not_in=set()):
        results = set()

        for inner_type in self.inner_types:
            results.add(inner_type)
            results |= inner_type.inner_types_all
        
        return {t for t in results if t.type_identifier not in type_not_in}

    @property
    def inner_types_all(self):
        return self.inner_types_all_filtered(type_not_in=set())


class ObjcTypeType():

    CLASS = 'class'
    CATEGORY = 'category'
    ENUM = 'enum'
    CONSTANT = 'constant'
    MACRO_CONSTANT = 'macro_constant'
    PROTOCOL = 'protocol'

    ALL = {
        CLASS,
        CATEGORY,
        ENUM,
        CONSTANT,
        MACRO_CONSTANT,
        PROTOCOL,
    }


class ObjcEnumType():

    NS_ENUM = 'NS_ENUM'
    NS_CLOSED_ENUM = 'NS_CLOSED_ENUM'
    NS_OPTIONS = 'NS_OPTIONS'
    NS_TYPED_ENUM = 'NS_TYPED_ENUM'
    NS_TYPED_EXTENSIBLE_ENUM = 'NS_TYPED_EXTENSIBLE_ENUM'

    ALL = {
        NS_ENUM,
        NS_CLOSED_ENUM,
        NS_OPTIONS,
        NS_TYPED_ENUM,
        NS_TYPED_EXTENSIBLE_ENUM,
    }


class ObjcInterface():
    
    def __init__(self, class_name, super_class_name):
        self.class_name = class_name
        self.super_class_name = super_class_name

    def __repr__(self):
        # We consider that an objective-c interface defines an objective-c class
        return '{:<15} {}'.format(ObjcTypeType.CLASS, self.class_name)


class ObjcType():

    def __init__(self, type_identifier, name, super_class_name=None, category_name=None):
        assert type_identifier in ObjcTypeType.ALL

        self.type_identifier = type_identifier
        self.name = name
        self.super_class_name = super_class_name
        self.category_name = category_name

        self.file = None

    def __repr__(self):
        return '{:<15} {}'.format(self.type_identifier, self.name)

    @property
    def fullname(self):
        return self.name

    def inherits_from_one_of(self, class_names):
        return self.super_class_name in class_names
