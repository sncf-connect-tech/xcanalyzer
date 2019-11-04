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

    def __init__(self, type_identifier, name, accessibility, inherited_types=set()):
        assert type_identifier in SwiftTypeType.ALL
        assert accessibility in SwiftAccessibility.ALL

        self.type_identifier = type_identifier
        self.name = name
        self.accessibility = accessibility
        self.inherited_types = inherited_types

        self.inner_types = list()

        self.used_types = set()
    
    def __repr__(self):
        return '{:<11} {:<9} {}'.format(self.accessibility, self.type_identifier, self.name)
    
    def __eq__(self, other):
        return self.type_identifier == other.type_identifier and \
            self.name == other.name and \
            self.accessibility == other.accessibility


class ObjcTypeType():

    CLASS = 'class'
    CATEGORY = 'category'
    ENUM = 'enum'
    CONSTANT = 'constant'
    PROTOCOL = 'protocol'

    ALL = {
        CLASS,
        CATEGORY,
        ENUM,
        CONSTANT,
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


class ObjcType():

    def __init__(self, type_identifier, name):
        assert type_identifier in ObjcTypeType.ALL

        self.type_identifier = type_identifier
        self.name = name

    def __repr__(self):
        return '{:<9} {}'.format(self.type_identifier, self.name)
