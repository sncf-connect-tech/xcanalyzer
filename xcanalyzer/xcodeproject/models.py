class XcFile():

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "<XcFile> {} [{}]".format(self.name, self.path)


class XcGroup():

    def __init__(self, group_path, filepath, groups=None, files=None, is_variant=False):
        self.group_path = group_path
        self.filepath = filepath
        self.groups = groups or list()
        self.files = files or set()
        self.is_variant = is_variant

    def __eq__(self, other):
        return self.group_path == other.group_path

    def __hash__(self):
        return hash(self.group_path)

    def __repr__(self):
        return "<XcGroup> {}".format(self.group_path)
    

class XcProject():

    def __init__(self, name, targets, groups, files):
        self.name = name
        self.targets = targets
        self.groups = groups
        self.files = files
    
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
    
    def group_paths(self, filter_mode=None):
        """ Returns the list of path sorted by name of all groups in the project. """

        results = []

        remaining_groups = list()

        for group in self.groups:
            remaining_groups.append(group)
        
        while remaining_groups:
            # Look for current group and its path
            current_group = remaining_groups.pop()
            current_path = current_group.group_path

            if filter_mode == 'empty':
                # Only empty folder
                if not current_group.groups and not current_group.files:
                    results.append(current_path)
            else:
                # Add current group path
                results.append(current_path)

            # Add its children to be treated
            for subgroup in current_group.groups:
                remaining_groups.append(subgroup)
            
        results.sort()
        return results


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
