

class XcProject():

    def __init__(self, name, targets):
        self.name = name
        self.targets = targets
    
    def targets_of_type(self, target_type):
        return set([t for t in self.targets if t.type == target_type])


class XcTarget():

    class Type():
        TEST = 'test'
        UI_TEST = 'uitest'
        FRAMEWORK = 'framework'
        EXTENSION = 'extension'
        APPLICATION = 'application'

    def __init__(self, name, target_type, dependencies=set()):
        self.name = name
        self.type = target_type
        self.dependencies = dependencies  # Set of targets

    def __eq__(self, other):
        if self.type != other.type:
            return False
        elif self.name != other.name:
            return False
        return True
    
    def __hash__(self):
        return hash((self.type, self.name))

    def __repr__(self):
        return "<XcTarget> {}".format(self.name)
