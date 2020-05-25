from ..language.models import SwiftTypeType, ObjcTypeType, SwiftExtensionScope, UI_VIEW_CONTROLLER_BASE_CLASSES


class XcFile():

    def __init__(self, filepath):
        self.filepath = filepath
        self.swift_types = None
        self.objc_types = None
        self.objc_interfaces = None

    def __eq__(self, other):
        return self.filepath == other.filepath

    def __hash__(self):
        return hash(self.filepath)

    def __repr__(self):
        return "<XcFile> {}".format(self.filepath)
    
    @property
    def filename(self):
        return self.filepath.split('/')[-1]

    def swift_types_filtered(self, type_not_in=set()):
        assert type_not_in.issubset(SwiftTypeType.ALL)

        return [t for t in self.swift_types if t.type_identifier not in type_not_in]
    
    def objc_types_filtered(self, type_not_in=set()):
        assert type_not_in.issubset(ObjcTypeType.ALL)

        return [t for t in self.objc_types if t.type_identifier not in type_not_in]
    
    @property
    def swift_extensions(self):
        return [t for t in self.swift_types if t.type_identifier == SwiftTypeType.EXTENSION]
    
    @property
    def swift_classes(self):
        return [t for t in self.swift_types if t.type_identifier == SwiftTypeType.CLASS]

    @property
    def objc_classes(self):
        return [t for t in self.objc_types if t.type_identifier == ObjcTypeType.CLASS]
    
    @property
    def is_swift(self):
        return self.filepath.endswith('.swift')

    @property
    def is_objc_h(self):
        return self.filepath.endswith('.h')

    @property
    def is_objc_m(self):
        return self.filepath.endswith('.m')

    @property
    def is_objc(self):
        return self.is_objc_h or self.is_objc_m

class XcGroup():

    def __init__(self,
                 group_path,
                 filepath,
                 is_project_relative=False,
                 groups=None,
                 files=None,
                 is_variant=False):
        self.group_path = group_path
        self.filepath = filepath
        self.is_project_relative = is_project_relative
        self.groups = groups or list()
        self.files = files or set()
        self.is_variant = is_variant

    def __eq__(self, other):
        return self.group_path == other.group_path

    def __hash__(self):
        return hash(self.group_path)

    def __repr__(self):
        return "<XcGroup> {} [{}]".format(self.group_path, self.filepath)
    
    @property
    def has_folder(self):
        return self.group_path == self.filepath
    

class XcProject():

    def __init__(self, dirpath, name, targets, groups, files):
        assert type(groups) == list

        self.dirpath = dirpath
        self.name = name
        self.targets = targets
        self.groups = groups
        self.root_files = files

        self.swift_files_parsed = False
        self.objc_files_parsed = False
    
    def targets_of_type(self, target_type):
        results = {t for t in self.targets if t.type == target_type}
        return sorted(results, key=lambda t: t.name)
    
    def target_with_name(self, name):
        candidates = [t for t in self.targets if t.name == name]

        if not candidates:
            return None
        
        return candidates[0]
    
    @property
    def target_files(self):
        results = set()

        for target in self.targets:
            results |= target.files
        
        return results
    
    @property
    def source_files(self):
        results = set()

        for target in self.targets:
            results |= target.swift_files
            results |= target.objc_files
        
        results |= self.target_less_h_files

        return results
    
    @property
    def target_less_files(self):
        return self.files - self.target_files
    
    @property
    def target_less_h_files(self):
        return set([f for f in self.target_less_files if f.is_objc_h])
    
    @property
    def group_files(self):
        results = set()

        groups = self.groups.copy()

        while groups:
            group = groups.pop()
            results |= group.files
            groups += group.groups
        
        return results
    
    @property
    def nonregular_files(self):
        results = list()

        groups = self.groups.copy()

        while groups:
            group = groups.pop()

            if group.is_variant:
                continue
            
            for group_file in group.files:
                if not group_file.filepath.startswith(group.group_path):
                    results.append((group_file, group))

            groups += group.groups
        
        return results

    @property
    def files(self):
        return self.root_files | self.group_files
    
    def relative_path_for_file(self, xc_file):
        return ''.join([self.dirpath, xc_file.filepath])
    
    def file_with_name(self, name):
        for xc_file in self.files:
            if xc_file.filename == name:
                return xc_file
        
        return None
    
    def groups_filtered(self, filter_mode=None):
        """ Returns the list of path sorted by name of all groups in the project. """

        results = []

        remaining_groups = list()

        for group in self.groups:
            remaining_groups.append(group)

        while remaining_groups:
            # Look for current group and its path
            current_group = remaining_groups.pop()

            # Empty groups
            if filter_mode == 'empty':
                if not current_group.groups and not current_group.files:
                    results.append(current_group)
            
            # Relative to project groups
            elif filter_mode == 'project_relative':
                if current_group.is_project_relative:
                    results.append(current_group)
            
            # Without folder groups
            elif filter_mode == 'without_folder':
                if not current_group.is_variant and not current_group.has_folder:
                    results.append(current_group)
                
            # Variant groups
            elif filter_mode == 'variant':
                if current_group.is_variant:
                    results.append(current_group)
            
            # All groups
            else:
                # Add current group path
                results.append(current_group)

            # Add its children to be treated
            for subgroup in current_group.groups:
                remaining_groups.append(subgroup)
        
        return results
    
    @property
    def target_objc_files(self):
        """ Union of targets' objc files and target .h files. """
        results = set()

        # .h and .m targets' files
        for target in self.targets:
            results |= target.objc_files
        
        # .h target less files
        results |= self.target_less_h_files
        
        return results
    
    @property
    def target_objc_types(self):
        results = []

        for objc_file in self.target_objc_files:
            results += objc_file.objc_types
        
        return results

    def target_objc_types_filtered(self, type_in=ObjcTypeType.ALL):
        assert type_in.issubset(ObjcTypeType.ALL)

        results = {objc_type_type: [] for objc_type_type in type_in}
        
        for objc_type in self.target_objc_types:
            if objc_type.type_identifier not in type_in:
                continue
            
            results[objc_type.type_identifier].append(objc_type)

        return results

    @property
    def target_swift_files(self):
        """ All targets' swift files. """
        results = set()

        for target in self.targets:
            results |= target.swift_files

        return results

    @property
    def target_swift_types(self):
        results = []
        
        for target in self.targets:
            results += target.swift_types
        
        return results
    
    def target_swift_types_filtered(self, type_in=SwiftTypeType.ALL, type_not_in=set(), flat=False):
        assert type_in.issubset(SwiftTypeType.ALL)
        assert type_not_in.issubset(SwiftTypeType.ALL)

        # `type_not_in` has priority
        if type_not_in:
            types = SwiftTypeType.ALL - type_not_in
        else:
            types = type_in

        grouped_results = {swift_type_type: [] for swift_type_type in types}
        
        for swift_type in self.target_swift_types:
            if swift_type.type_identifier not in types:
                continue
            
            grouped_results[swift_type.type_identifier].append(swift_type)

        if flat:
            results = []

            for swift_types in grouped_results.values():
                results += list(swift_types)

            return results
        else:
            return grouped_results
        
    @property
    def target_swift_extensions_grouped_by_scope(self):
        file_scoped_extensions = []
        remaining_extensions = []

        # File scoped extensions
        for swift_file in self.target_swift_files:
            for swift_extension in swift_file.swift_extensions:
                non_extension_swift_types = swift_file.swift_types_filtered(type_not_in={SwiftTypeType.EXTENSION})

                if swift_extension.name in [t.name for t in non_extension_swift_types]:
                    file_scoped_extensions.append(swift_extension)
                else:
                    remaining_extensions.append(swift_extension)
        
        # Project-scoped extensions: Objc and swift
        objc_type_names = [t.name for t in self.target_objc_types]
        swift_type_names = [t.name for t in self.target_swift_types_filtered(type_not_in={SwiftTypeType.EXTENSION}, flat=True)]

        objc_scoped_extensions = []
        swift_scoped_extensions = []
        outer_extensions = []
        
        remaining_extensions.reverse()
        while remaining_extensions:
            extension = remaining_extensions.pop()
            if extension.name in objc_type_names:
                objc_scoped_extensions.append(extension)
            elif extension.name in swift_type_names:
                swift_scoped_extensions.append(extension)
            else:
                # Outer scoped extensions
                outer_extensions.append(extension)
        
        return {
            SwiftExtensionScope.FILE: file_scoped_extensions,
            SwiftExtensionScope.PROJECT_OBJC: objc_scoped_extensions,
            SwiftExtensionScope.PROJECT_SWIFT: swift_scoped_extensions,
            SwiftExtensionScope.OUTER: outer_extensions,
        }


class XcBuildSetting():

    def __init__(self, key, value):
        # value must be a list of str
        self.key = key
        self.value = value


class XcBuildConfiguration():

    def __init__(self, name, build_settings):  # TODO: base reference build file
        self.name = name
        self.build_settings = build_settings


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
                 product_name,
                 build_configurations,
                 dependencies=None,
                 linked_frameworks=None,
                 embed_frameworks=None,
                 source_files=None,
                 resource_files=None,
                 header_files=None,
                 linked_files=None):
        self.name = name
        self.type = target_type
        self.product_name = product_name
        self.build_configurations = build_configurations
        self.dependencies = dependencies or set()  # Set of targets
        self.linked_frameworks = linked_frameworks or set()  # Set of targets
        self.embed_frameworks = embed_frameworks or set()  # Set of targets
        self.source_files = source_files or set()
        self.resource_files = resource_files or set()
        self.header_files = header_files or set()
        self.linked_files = linked_files or set()

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
    
    @property
    def files(self):
        return self.source_files | self.resource_files | self.header_files | self.linked_files
    
    @property
    def swift_files(self):
        return set([f for f in self.source_files if f.is_swift])
    
    @property
    def h_files(self):
        return set([f for f in self.header_files if f.is_objc_h])

    @property
    def m_files(self):
        return set([f for f in self.source_files if f.is_objc_m])

    @property
    def objc_files(self):
        return self.h_files | self.m_files
    
    @property
    def dependencies_all(self):
        result = set()

        # Direct dependencies
        result.update(self.dependencies)

        # Indirect dependencies
        for dependency in self.dependencies:
            result.update(dependency.dependencies)

        return result
    
    @property
    def dependant_source_files(self):
        results = set()

        results |= self.swift_files
        results |= self.objc_files

        for target in self.dependencies_all:
            results |= target.swift_files
            results |= target.objc_files
        
        return results

    # Swift types

    def swift_types_filtered(self, type_not_in=set()):
        assert type_not_in.issubset(SwiftTypeType.ALL)

        results = set()
        
        for swift_file in self.swift_files:
            results |= set(swift_file.swift_types_filtered(type_not_in=type_not_in))
                
            for swift_type in swift_file.swift_types:
                results |= swift_type.inner_types_all_filtered(type_not_in=type_not_in)
        
        return results

    @property
    def swift_types(self):
        return self.swift_types_filtered(type_not_in=set())
    
    def swift_types_dependencies_filtered(self, type_not_in=set()):
        """ Return, filtered by given filter, Swift types of self and all its target dependencies. """
        assert type_not_in.issubset(SwiftTypeType.ALL)

        results = set()
        
        for target_dependency in self.dependencies_all:
            results |= target_dependency.swift_types_filtered(type_not_in=type_not_in)
        
        results |= self.swift_types_filtered(type_not_in=type_not_in)

        return results

    # Objective-C types

    def objc_types_filtered(self, type_not_in=set()):
        assert type_not_in.issubset(ObjcTypeType.ALL)

        results = set()
        
        for objc_file in self.objc_files:
            results |= set(objc_file.objc_types_filtered(type_not_in=type_not_in))
                
        return results

    @property
    def objc_types(self):
        return self.objc_types_filtered(type_not_in=set())

    def objc_types_dependencies_filtered(self, type_not_in=set()):
        """ Return, filtered by given filter, Objective-C types of self and all its target dependencies. """
        assert type_not_in.issubset(ObjcTypeType.ALL)

        results = set()
        
        for target_dependency in self.dependencies_all:
            results |= target_dependency.objc_types_filtered(type_not_in=type_not_in)
        
        results |= self.objc_types_filtered(type_not_in=type_not_in)

        return results

    @property
    def swift_types_grouped_by_type(self):
        results = dict()

        for swift_type_type in SwiftTypeType.ALL:
            results[swift_type_type] = []

        for swift_type in self.swift_types:
            results[swift_type.type_identifier].append(swift_type)

        return results

    @property
    def objc_types_grouped_by_type(self):
        results = dict()

        for objc_type_type in ObjcTypeType.ALL:
            results[objc_type_type] = []

        for objc_type in self.objc_types:
            results[objc_type.type_identifier].append(objc_type)

        return results

    @property
    def swift_classes(self):
        results = []
        
        for swift_file in self.swift_files:
            results += swift_file.swift_classes
        
        return results

    @property
    def objc_classes(self):
        results = []
        
        for objc_file in self.objc_files:
            results += objc_file.objc_classes
        
        return results

    @property
    def view_controllers(self):
        results = []

        swift_classes = self.swift_classes
        objc_classes = self.objc_classes
        next_swift_classes = []
        next_objc_classes = []

        # View controllers that inherit from UIViewController directly
        for swift_class in swift_classes:
            if swift_class.inherits_from_view_controller:
                results.append(swift_class)
            else:
                next_swift_classes.append(swift_class)
        for objc_class in objc_classes:
            if objc_class.super_class_name in UI_VIEW_CONTROLLER_BASE_CLASSES:
                results.append(objc_class)
            else:
                next_objc_classes.append(objc_class)
        
        swift_classes = next_swift_classes
        objc_classes = next_objc_classes
        next_swift_classes = []
        next_objc_classes = []

        # View controllers that inherit from other view controllers
        # defined in a direct dependency
        dependency_view_controllers = set()
        for dependency in self.dependencies:
            dependency_view_controllers |= {vc.name for vc in dependency.view_controllers}

        for swift_class in swift_classes:
            if swift_class.inherits_from_one_of(dependency_view_controllers):
                results.append(swift_class)
            else:
                next_swift_classes.append(swift_class)
        for objc_class in objc_classes:
            if objc_class.inherits_from_one_of(dependency_view_controllers):
                results.append(objc_class)
            else:
                next_objc_classes.append(objc_class)
        
        swift_classes = next_swift_classes
        objc_classes = next_objc_classes
        next_swift_classes = []
        next_objc_classes = []

        # View controllers that inherit from the previous sets
        detected_view_controllers = {r.name for r in results}

        new_detected_view_controllers = True
        while new_detected_view_controllers:
            new_detected_view_controllers = False

            for swift_class in swift_classes:
                if swift_class.inherits_from_one_of(detected_view_controllers):
                    results.append(swift_class)
                    detected_view_controllers.add(swift_class.name)
                    new_detected_view_controllers = True
                else:
                    next_swift_classes.append(swift_class)
            
            for objc_class in objc_classes:
                if objc_class.inherits_from_one_of(detected_view_controllers):
                    results.append(objc_class)
                    detected_view_controllers.add(objc_class.name)
                    new_detected_view_controllers = True
                else:
                    next_objc_classes.append(objc_class)
        
            swift_classes = next_swift_classes
            objc_classes = next_objc_classes
            next_swift_classes = []
            next_objc_classes = []

        return results


