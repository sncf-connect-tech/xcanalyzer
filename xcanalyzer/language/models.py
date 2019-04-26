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

    def __init__(self, type_identifier, name, accessibility):
        assert type_identifier in SwiftTypeType.ALL
        assert accessibility in SwiftAccessibility.ALL

        self.type_identifier = type_identifier
        self.name = name
        self.accessibility = accessibility
    
    def __repr__(self):
        return '{:<11} {:<9} {}'.format(self.accessibility, self.type_identifier, self.name)


class ObjcTypeType():

    CLASS = 'class'
    CATEGORY = 'category'
    ENUM = 'enum'
    PROTOCOL = 'protocol'

    ALL = {
        CLASS,
        CATEGORY,
    }


class ObjcType():

    def __init__(self, type_identifier, name):
        assert type_identifier in ObjcTypeType.ALL

        self.type_identifier = type_identifier
        self.name = name

    def __repr__(self):
        return '{:<9} {}'.format(self.type_identifier, self.name)
