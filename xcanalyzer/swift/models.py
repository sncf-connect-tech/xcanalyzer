class SwiftAccessibility():

    PRIVATE = 'private'
    FILEPRIVATE = 'fileprivate'
    INTERNAL = 'internal'
    PUBLIC = 'public'


class SwiftTypeType():

    PROTOCOL = 'protocol'
    EXTENSION = 'extension'
    STRUCT = 'struct'
    ENUM = 'enum'
    CLASS = 'class'


class SwiftType():

    def __init__(self, type_identifier, name, accessibility):
        self.type_identifier = type_identifier
        self.name = name
        self.accessibility = accessibility
    
    def __repr__(self):
        return '{:<11} {:<9} {}'.format(self.accessibility, self.type_identifier, self.name)
