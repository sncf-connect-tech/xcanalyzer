

class XcProject():

    def __init__(self, name, targets):
        self.name = name
        self.targets = targets
    
    def targets_of_type(self, target_type):
        results = {t for t in self.targets if t.type == target_type}
        return sorted(results, key=lambda t: t.name)


class XcTarget():

    class Type():
        TEST = 'test'
        UI_TEST = 'ui_test'
        FRAMEWORK = 'framework'
        APP_EXTENSION = 'app_extension'
        WATCH_EXTENSION = 'watch_extension'
        APPLICATION = 'application'

        AVAILABLES = [
            FRAMEWORK,
            APP_EXTENSION,
            WATCH_EXTENSION,
            APPLICATION,
            TEST,
            UI_TEST,
        ]

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
