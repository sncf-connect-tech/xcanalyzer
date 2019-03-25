class XcGroup():

    def __init__(self, name, groups=None):
        self.name = name
        self.groups = groups or set()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "<XcGroup> {}".format(self.name)
    

class XcProject():

    def __init__(self, name, targets, groups):
        self.name = name
        self.targets = targets
        self.groups = groups
    
    def targets_of_type(self, target_type):
        results = {t for t in self.targets if t.type == target_type}
        return sorted(results, key=lambda t: t.name)
    
    def target_with_name(self, name):
        candidates = [t for t in self.targets if t.name == name]

        if not candidates:
            return None
        
        return candidates[0]
    
    @property
    def targets_sorted_by_name(self):
        results = list(self.targets)
        return sorted(results, key=lambda t: t.name)


class XcTarget():

    class Type():
        TEST = 'test'
        UI_TEST = 'ui_test'
        FRAMEWORK = 'framework'
        APP_EXTENSION = 'app_extension'
        WATCH_EXTENSION = 'watch_extension'
        APPLICATION = 'application'
        WATCH_APPLICATION = 'watch_application'
        OTHER = 'other'

        AVAILABLES = [  # Default order of display
            FRAMEWORK,
            APP_EXTENSION,
            WATCH_EXTENSION,
            WATCH_APPLICATION,
            APPLICATION,
            TEST,
            UI_TEST,
            OTHER,
        ]

    def __init__(self,
                 name,
                 target_type,
                 dependencies=None,
                 source_files=None,
                 resource_files=None):
        self.name = name
        self.type = target_type
        self.dependencies = dependencies or set()  # Set of targets
        self.source_files = source_files or set()
        self.resource_files = resource_files or set()

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
