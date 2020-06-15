import errno
import json
import pickle
import os
import re
import subprocess

import openstep_parser as osp
from pbxproj import XcodeProject

from ..language.models import SwiftType, SwiftTypeType, SwiftAccessibility, ObjcTypeType, ObjcType, ObjcEnumType, ObjcInterface

from .exceptions import XcodeProjectReadException
from .models import XcTarget, XcProject, XcGroup, XcFile, XcBuildSetting, XcBuildConfiguration


class XcProjectParser():

    def __init__(self,
                 project_folder_path,
                 verbose=True,
                 working_dir_relative=False,
                 cache_active=True):
        self.project_folder_path = project_folder_path
        self.verbose = verbose
        self.working_dir_relative = working_dir_relative
        self.cache_active = cache_active

    def load(self):
        # Check given path
        self._check_folder_path()

        # Find xcode proj folder
        self.xcode_proj_name = self._find_xcodeproj()

        # Create working directory if relative to project dir
        if self.working_dir_relative:
            working_dir = os.path.join(self.project_folder_path, 'build')
            try:
                os.makedirs(working_dir)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(working_dir):
                    pass
                else:
                    raise

        # Load pbxproj
        pbxproj_path = '{}/{}/project.pbxproj'.format(self.project_folder_path, self.xcode_proj_name)

        # Load from cache if existing
        if self.cache_active:
            xc_project_from_cache = self.load_from_cache()
            if xc_project_from_cache is not None:
                if self.verbose:
                    print("-> Load pbxproj from cache")
                self.xc_project = xc_project_from_cache
                return

        if self.verbose:
            print("-> Load pbxproj")

        # Open pbxproj
        with open(pbxproj_path, 'r') as f:  # To avoid ResourceWarning: unclosed file
            tree = osp.OpenStepDecoder.ParseFromFile(f)
            self.xcode_project = XcodeProject(tree, pbxproj_path)

        self.file_mapping = dict()

        # Files a project root
        if self.verbose:
            print("-> Find root files")
        root_files = self._find_root_files()

        # Output object
        self.xc_project = XcProject(self.project_folder_path,
                                    self.xcode_proj_name,
                                    build_configurations=list(),
                                    targets=list(),
                                    groups=list(),
                                    files=root_files)

        # Project build settings (from build configurations)
        if self.verbose:
            print("-> Parse project build configurations")
        self.xc_project.build_configurations = self._parse_project_build_configurations()

        # Groups
        if self.verbose:
            print("-> Parse groups")
        self.xc_project.groups = self._parse_groups()

        # Tests, extensions and app modules
        if self.verbose:
            print("-> Parse targets")
        self.xc_project.targets = self._parse_targets()

        if self.verbose:
            print("=> Xcode project loading finished.")

        self.save_project_to_cache()
    
    @property
    def cache_filepath(self):
        command = ['git', '-C', self.project_folder_path, 'rev-parse', 'HEAD']
        result = subprocess.run(command, capture_output=True)
        git_ref = result.stdout.decode()[:8]
        
        return 'build/{}_{}.pkl'.format(self.xcode_proj_name, git_ref)

    def save_project_to_cache(self):
        with open(self.cache_filepath, 'wb') as output:
            pickle.dump(self.xc_project, output, pickle.HIGHEST_PROTOCOL)

    def load_from_cache(self):
        if not os.path.exists(self.cache_filepath):
            return None

        with open(self.cache_filepath, 'rb') as input_data:
            return pickle.load(input_data)

    def parse_swift_files(self):
        if self.xc_project.swift_files_parsed:
            return

        if self.verbose:
            print("-> Parse Swift files.")

        for target in self.xc_project.targets:
            for swift_file in target.swift_files:
                parser = SwiftFileParser(project_folder_path=self.xc_project.dirpath,
                                         xc_file=swift_file)
                parser.parse()
        
        if self.verbose:
            print("=> Swift files parsing finished.")
        
        self.xc_project.swift_files_parsed = True

        self.save_project_to_cache()
    
    def parse_objc_files(self):
        if self.xc_project.objc_files_parsed:
            return

        if self.verbose:
            print("-> Parse Objective-C files.")

        objc_super_class_names = dict()

        # Targets' objective-C files
        for target in self.xc_project.targets:
            for objc_file in target.objc_files:
                parser = ObjcFileParser(xc_project=self.xc_project,
                                        xc_file=objc_file)
                parser.parse()

                for objc_interface in objc_file.objc_interfaces:
                    objc_super_class_names[objc_interface.class_name] = objc_interface.super_class_name
        
        # Target less objective-C files
        for objc_file in self.xc_project.target_less_h_files:
            parser = ObjcFileParser(xc_project=self.xc_project,
                                    xc_file=objc_file)
            parser.parse()

            for objc_interface in objc_file.objc_interfaces:
                objc_super_class_names[objc_interface.class_name] = objc_interface.super_class_name
        
        # Set superclass to classes
        for target in self.xc_project.targets:
            for objc_file in target.objc_files:
                for objc_class in objc_file.objc_classes:
                    objc_class.super_class_name = objc_super_class_names.get(objc_class.name)

        if self.verbose:
            print("=> Objective-C files parsing finished.")
        
        self.xc_project.objc_files_parsed = True

        self.save_project_to_cache()

    def _check_folder_path(self):
        if not os.path.isdir(self.project_folder_path):
            raise XcodeProjectReadException("Folder not found: {}".format(self.project_folder_path))

    def _find_xcodeproj(self):
        files = os.listdir(self.project_folder_path)
        
        for filename in files:
            if filename.endswith('xcodeproj'):
                return filename
        
        raise XcodeProjectReadException("No '.xcodeproj' folder found in folder: {}".format(self.project_folder_path))

    def _map_target_type(self, target):
        if target.productType.startswith('com.apple.product-type.app-extension'):
            return XcTarget.Type.APP_EXTENSION
        
        return {
            'com.apple.product-type.bundle.unit-test': XcTarget.Type.TEST,
            'com.apple.product-type.bundle.ui-testing': XcTarget.Type.UI_TEST,
            'com.apple.product-type.framework': XcTarget.Type.FRAMEWORK,
            'com.apple.product-type.watchkit2-extension': XcTarget.Type.WATCH_EXTENSION,
            'com.apple.product-type.application': XcTarget.Type.APPLICATION,
            'com.apple.product-type.application.watchapp2': XcTarget.Type.WATCH_APPLICATION,
        }.get(target.productType, XcTarget.Type.OTHER)
    
    def _map_target_build_configurations(self, buildConfigurationList):
        build_configuration_list = self.xcode_project.get_object(buildConfigurationList)

        result_build_configurations = list()
        
        for build_configuration_id in build_configuration_list.buildConfigurations:
            build_configuration = self.xcode_project.get_object(build_configuration_id)

            result_build_settings = list()
            
            build_config_keys = build_configuration.buildSettings.get_keys()
            for setting_key in build_config_keys:
                setting_value = getattr(build_configuration.buildSettings, setting_key)
                if type(setting_value) == str:
                    result_build_setting = XcBuildSetting(setting_key, [setting_value])
                else:  # expected to be a list of str
                    result_build_setting = XcBuildSetting(setting_key, setting_value)
                
                result_build_settings.append(result_build_setting)
            
            result_build_configuration = XcBuildConfiguration(build_configuration.name,
                                                              result_build_settings)
            result_build_configurations.append(result_build_configuration)
        
        return result_build_configurations

    @property
    def _main_group(self):
        project_object = self.xcode_project.get_object(self.xcode_project.rootObject)
        assert project_object.isa == 'PBXProject'
        
        main_group = self.xcode_project.get_object(project_object.mainGroup)
        assert main_group.isa == 'PBXGroup'

        return main_group

    def _file_name_for_file_ref(self, file_ref, of_variant=False):
        assert file_ref.isa == 'PBXFileReference'

        if of_variant:
            return file_ref.path.split('/')[-1]
        else:
            if hasattr(file_ref, 'name'):
                return file_ref.name
            else:
                return file_ref.path

    def _find_root_files(self):
        results = set()

        for child_key in self._main_group.children:
            child = self.xcode_project.get_object(child_key)
            if child.isa == 'PBXFileReference':
                filename = self._file_name_for_file_ref(child)
                filepath = self._reduce_double_dot_filepath_part('/{}'.format(filename))
                xc_file = XcFile(filepath=filepath)
                results.add(xc_file)
                self.file_mapping[child] = xc_file

        return results

    def _reduce_double_dot_filepath_part(self, filepath):
        new_parts = []
        parts = filepath.split('/')

        # Last part: filename
        new_parts.append(parts.pop())

        double_dot_count = 0

        while parts:
            part = parts.pop()  # Right most part

            if part == '..':
                double_dot_count += 1

                # Check that previous parts are sufficiently numerous
                assert double_dot_count <= len(parts)
            elif double_dot_count != 0:
                double_dot_count -= 1
            else:
                new_parts.append(part)
        
        new_parts.reverse()
        return '/'.join(new_parts)
    
    def _parse_project_build_configurations(self):
        root = self.xcode_project.get_object(self.xcode_project.rootObject)
        return self._map_target_build_configurations(root.buildConfigurationList)

    def _parse_groups(self):
        # key is a child key reference
        # value is a tuple:
        #   the XcGroup destination of the parent
        #   the path of parent
        children_to_treat = dict()

        root_group = XcGroup('', '')
        for child_key in self._main_group.children:
            child = self.xcode_project.get_object(child_key)
            if child.isa != 'PBXGroup':
                continue
            children_to_treat[child_key] = (root_group, '')

        while children_to_treat:
            current_child_key = list(children_to_treat.keys())[0]
            parent_group, parent_filepath = children_to_treat.pop(current_child_key)
            current_child = self.xcode_project.get_object(current_child_key)

            if current_child.isa in {'PBXGroup', 'PBXVariantGroup'}:  # Child is a group
                # Compute current child filepath
                if current_child.sourceTree == '<group>':  # Relative to group
                    if hasattr(current_child, 'path'):
                        current_filepath = '/'.join([parent_filepath, current_child.path])
                    else:
                        current_filepath = parent_filepath  # current group without folder
                    is_project_relative = False
                
                elif current_child.sourceTree == 'SOURCE_ROOT':  # Relative to project
                    current_filepath = '/{}'.format(current_child.path)
                    is_project_relative = True

                # Current child group path
                if hasattr(current_child, 'name'):
                    name = current_child.name
                else:
                    name = current_child.path
                current_group_path = '/'.join([parent_group.group_path, name])

                # Link the parent with its child
                is_variant = current_child.isa == 'PBXVariantGroup'
                current_group = XcGroup(current_group_path,
                                        current_filepath,
                                        is_project_relative=is_project_relative,
                                        is_variant=is_variant)

                parent_group.groups.append(current_group)

                # Add this child's children for treatment
                for child_key in current_child.children:
                    children_to_treat[child_key] = (current_group, current_filepath)

                # File mapping to be used foreward in targets parsing
                self.file_mapping[current_child] = current_group

            elif current_child.isa == 'PBXFileReference':  # Child is a file reference
                if current_child.sourceTree == '<group>':  # Relative to group
                    current_filepath = '/'.join([parent_filepath, current_child.path])
            
                elif current_child.sourceTree == 'SOURCE_ROOT':  # Relative to project
                    current_filepath = '/{}'.format(current_child.path)
                
                else:
                    # Ignore other files (ex: *.app from build product dir)
                    continue

                current_filepath = self._reduce_double_dot_filepath_part(current_filepath)

                xc_file = XcFile(filepath=current_filepath)
                parent_group.files.add(xc_file)

                # File mapping to be used foreward in targets parsing
                self.file_mapping[current_child] = xc_file
        
        return root_group.groups

    def _parse_targets(self):
        targets = self.xcode_project.objects.get_targets()

        xcode_targets = set()

        target_dependencies_names = dict()

        product_references = dict()
        target_linked_framework_refs = dict()
        target_embed_framework_refs = dict()

        for target in targets:
            # Test modules
            xcode_target_type = self._map_target_type(target)

            # Product name
            # We don't use target.productName because its seems to not be used by Xcode
            product_name = self.xcode_project.get_object(target.productReference).path

            # Build configuration list
            build_configurations = self._map_target_build_configurations(target.buildConfigurationList)

            # Transform into XcTarget
            xcode_target = XcTarget(target.name,
                                    xcode_target_type,
                                    product_name=product_name,
                                    build_configurations=build_configurations,
                                    dependencies=set(),
                                    source_files=set())
            xcode_targets.add(xcode_target)

            # Product reference
            product_references[target.productReference] = xcode_target

            # Find target's dependencies
            dependencies_names = set()
            pbxproj_dependencies = [self.xcode_project.get_object(dep_key) for dep_key in target.dependencies]
            dependencies_names = [self.xcode_project.get_object(dep.target).name for dep in pbxproj_dependencies]
            target_dependencies_names[target.name] = dependencies_names

            # Find file for each target
            for build_phase_key in target.buildPhases:
                build_phase = self.xcode_project.get_object(build_phase_key)

                # Sources files
                if build_phase.isa == 'PBXSourcesBuildPhase':
                    for build_file_key in build_phase.files:
                        build_file = self.xcode_project.get_object(build_file_key)
                        file_ref = self.xcode_project.get_object(build_file.fileRef)

                        if file_ref.isa == 'PBXVariantGroup':  # Localized source files (ex: intentdefinition)
                            for child in file_ref.children:
                                variant_file_ref = self.xcode_project.get_object(child)
                                xcode_target.source_files.add(self.file_mapping[variant_file_ref])
                        else:
                            xcode_target.source_files.add(self.file_mapping[file_ref])

                # Resources files
                elif build_phase.isa == 'PBXResourcesBuildPhase':
                    for build_file_key in build_phase.files:
                        build_file = self.xcode_project.get_object(build_file_key)
                        file_ref = self.xcode_project.get_object(build_file.fileRef)

                        if file_ref.isa == 'PBXVariantGroup':  # Localized resource files
                            for child in file_ref.children:
                                variant_file_ref = self.xcode_project.get_object(child)
                                xcode_target.resource_files.add(self.file_mapping[variant_file_ref])
                        else:
                            xcode_target.resource_files.add(self.file_mapping[file_ref])
                
                # Header files
                elif build_phase.isa == 'PBXHeadersBuildPhase':
                    for build_file_key in build_phase.files:
                        build_file = self.xcode_project.get_object(build_file_key)
                        file_ref = self.xcode_project.get_object(build_file.fileRef)
                        xcode_target.header_files.add(self.file_mapping[file_ref])

                # Find target's linked frameworks
                elif build_phase.isa == 'PBXFrameworksBuildPhase':
                    target_linked_framework_refs[xcode_target] = []
                    
                    for build_file_key in build_phase.files:
                        build_file = self.xcode_project.get_object(build_file_key)
                        
                        # Store for linked framework target dependencies
                        target_linked_framework_refs[xcode_target].append(build_file.fileRef)
                        
                        file_ref = self.xcode_project.get_object(build_file.fileRef)
                        
                        # Store as a library linked with binary of the target
                        if file_ref.sourceTree in {'<group>', 'SOURCE_ROOT'}:
                            xcode_target.linked_files.add(self.file_mapping[file_ref])
                
                # Find target's embed frameworks
                elif build_phase.isa == 'PBXCopyFilesBuildPhase':
                    target_embed_framework_refs[xcode_target] = [self.xcode_project.get_object(build_file).fileRef for build_file in build_phase.files]

        # Set dependencies for each target        
        for target_name, dependencies_names in target_dependencies_names.items():
            target = [t for t in xcode_targets if t.name == target_name][0]
            dependencies_targets = {t for t in xcode_targets if t.name in dependencies_names}

            target.dependencies = dependencies_targets
        
        # Set linked frameworks for each target
        for xcode_target, linked_framework_refs in target_linked_framework_refs.items():
            xcode_target.linked_frameworks = set()

            for linked_framework_ref in linked_framework_refs:
                # We avoid frameworks that are not a product of one project's target
                if linked_framework_ref in product_references:
                    xcode_target.linked_frameworks.add(product_references[linked_framework_ref])
    
        # Set embed frameworks for each target
        for xcode_target, embed_framework_refs in target_embed_framework_refs.items():
            xcode_target.embed_frameworks = set()

            for embed_framework_ref in embed_framework_refs:
                # We avoid frameworks that are not a product of one project's target
                if embed_framework_ref in product_references:
                    xcode_target.embed_frameworks.add(product_references[embed_framework_ref])
    
        # Sort target by name
        return sorted(list(xcode_targets), key=lambda t: t.name)
    
    def _find_type(self, swift_objc_type_name):
        for target in self.xc_project.targets:
            for swift_file in target.swift_files:
                for swift_type in swift_file.swift_types:
                    if swift_type.type_identifier != SwiftTypeType.EXTENSION and swift_type.name == swift_objc_type_name:
                        return swift_type

            for objc_file in target.objc_files:
                for objc_type in objc_file.objc_types:
                    if objc_type.name == swift_objc_type_name:
                        return objc_type

        for objc_file in self.xc_project.target_less_h_files:
            for objc_type in objc_file.objc_types:
                if objc_type.type_identifier != ObjcTypeType.CATEGORY and objc_type.name == swift_objc_type_name:
                    return objc_type
        
        return None
    
    def _find_files_that_contains(self, swift_objc_types, source_files):
        assert type(swift_objc_types) == set
        assert type(source_files) == set

        swift_objc_types = list(swift_objc_types)

        # Prepare occurrences
        occurrences = list()
        for swift_objc_type in swift_objc_types:
            occurrence = TypeOccurrencesFromFile(swift_or_objc_type=swift_objc_type,
                                                 source_files_that_use=set(),  # filled in the following lines
                                                 occurrences_count_in_definition_file=0)  # filled in the following lines
            occurrences.append(occurrence)
        
        # Regex
        regex = list()
        for swift_objc_type in swift_objc_types:
            # TODO: manage case of inner types: full name
            pattern = re.compile(r'^(?!//).*\W{}\W'.format(swift_objc_type.name))
            regex.append(pattern)
        
        source_files_count = len(source_files)
        for file_index, source_file in enumerate(source_files):
            xc_filepath = self.xc_project.relative_path_for_file(source_file)

            if self.verbose:
                print('{}/{} Searching: {}'.format(file_index + 1, source_files_count, xc_filepath))
            
            with open(xc_filepath) as opened_file:
                for line in opened_file:
                    if line.startswith('//'):  # optimization
                        continue

                    for (index, swift_objc_type) in enumerate(swift_objc_types):
                        if swift_objc_type.name not in line:  # optimization
                            continue
                        
                        if not regex[index].search(line):
                            continue

                        if swift_objc_type.file == source_file:
                            occurrences[index].occurrences_count_in_definition_file += 1
                        else:
                            occurrences[index].source_files_that_use.add(source_file)

        return occurrences

    def _find_occurrences_from_swift_file(self,
                                          opened_file,
                                          source_file,
                                          swift_objc_types,
                                          declarations_regex,
                                          occurrences_regex,
                                          occurrences):
        # Processing data: current type we're in
        current_types = list()
        bracket_counters = list()

        for line in opened_file:
            if line.startswith('//'):  # we ignore the line if it is a commented one
                continue

            found_declaration_type_in_line = None
            found_types_in_line = []

            for (index, swift_objc_type) in enumerate(swift_objc_types):
                if swift_objc_type.name not in line:  # optimization
                    continue

                # Declaration occurrence
                declaration_search = declarations_regex[index].search(line)
                if declaration_search:
                    if found_declaration_type_in_line:
                        raise Exception("Already found declaration of a type in this line!")
                    found_declaration_type_in_line = swift_objc_type

                # Other occurrences
                elif occurrences_regex[index].search(line):
                    found_types_in_line.append((index, swift_objc_type))

                    # TODO: Manage case of multi match in the same line
                
            # Manage current type
            if found_declaration_type_in_line:
                current_types.append(found_declaration_type_in_line)
                bracket_counters.append(0)
            
            # Found types
            for (index, found_type) in found_types_in_line:
                if current_types:
                    if found_type == current_types[-1]:
                        occurrences[index].occurrences_count_in_type_body += 1
                    else:
                        occurrences[index].swift_objc_types_that_use.add(current_types[-1])
                else:
                    occurrences[index].files_that_use.add(source_file)

            # Manage end of declaration type through the lines
            if current_types:
                for character in line:
                    if character == '{':
                        bracket_counters[-1] += 1
                    elif character == '}':
                        bracket_counters[-1] -= 1
                
                if bracket_counters[-1] == 0:
                    current_types.pop()
                    bracket_counters.pop()


    def _find_types_that_contains(self, swift_objc_types, source_files):
        assert type(swift_objc_types) == set
        assert type(source_files) == set

        # Remove duplicate types
        swift_objc_types = list(swift_objc_types)

        # Prepare occurrences
        occurrences = list()
        for swift_objc_type in swift_objc_types:
            occurrence = TypeOccurrencesFromType(swift_or_objc_type=swift_objc_type,
                                                 swift_objc_types_that_use=set(),  # filled in the following lines
                                                 occurrences_count_in_type_body=0,  # filled in the following lines
                                                 files_that_use=set())  # filled in the following lines
            occurrences.append(occurrence)
        
        # Regex
        declarations_regex = list()
        occurrences_regex = list()
        for swift_objc_type in swift_objc_types:
            # Type declaration regex
            declaration_pattern = re.compile(r'(^|\W){} +{}\W'.format(swift_objc_type.type_identifier, swift_objc_type.name))
            declarations_regex.append(declaration_pattern)

            # Occurrence regex
            occurrence_pattern = re.compile(r'\W{}\W'.format(swift_objc_type.fullname))
            occurrences_regex.append(occurrence_pattern)

        # TODO: manage type aliases
        # TODO: manage extensions and categories

        source_files_count = len(source_files)
        for file_index, source_file in enumerate(source_files):
            xc_filepath = self.xc_project.relative_path_for_file(source_file)
            print('{}/{} Searching: {}'.format(file_index + 1, source_files_count, xc_filepath))

            with open(xc_filepath) as opened_file:
                if source_file.is_swift:
                    self._find_occurrences_from_swift_file(opened_file,
                                                           source_file,
                                                           swift_objc_types,
                                                           declarations_regex,
                                                           occurrences_regex,
                                                           occurrences)
                        
        return occurrences

    def find_type_and_occurrences_from_files(self, swift_objc_type_name):
        # Check the type exist in the project
        found_type = self._find_type(swift_objc_type_name)

        if found_type is None:
            raise ValueError("Type not found in the Xcode project: '{}'".format(swift_objc_type_name))

        # Find files in which the type occurs
        return self._find_files_that_contains(set([found_type]), self.xc_project.source_files)[0]

    def find_type_occurrences_from_files(self, swift_objc_types, from_target):
        source_files = from_target.dependant_source_files | self.xc_project.target_less_h_files

        return self._find_files_that_contains(swift_objc_types, source_files)
    
    def find_type_occurrences_from_types(self, swift_objc_type_name, from_target):
        # Check the type exist in the project
        found_type = self._find_type(swift_objc_type_name)

        if found_type is None:
            raise ValueError("Type not found in the Xcode project: '{}'".format(swift_objc_type_name))

        # Source files in which to search for types occurrences
        source_files = from_target.dependant_source_files | self.xc_project.target_less_h_files

        # Find types in which the type occurs
        swift_types = from_target.swift_types_dependencies_filtered(type_not_in={SwiftTypeType.EXTENSION})
        objc_types = from_target.objc_types_dependencies_filtered(type_not_in={ObjcTypeType.CATEGORY})

        # types = swift_types | objc_types

        types = swift_types

        return self._find_types_that_contains(types, source_files)
    
    def _find_duplicate_swift_names(self, swift_types):
        swift_names_by_type_identifier = dict()

        type_identifiers = SwiftTypeType.ALL - {SwiftTypeType.EXTENSION}

        for type_identifier in type_identifiers:
            swift_names_by_type_identifier[type_identifier] = dict()
        
        for swift_type in swift_types:
            name = swift_type.fullname
            swift_names = swift_names_by_type_identifier[swift_type.type_identifier]

            if name not in swift_names:
                swift_names[name] = list()
            swift_names[name].append(swift_type)
        
        # Results
        results = list()

        for type_identifier in type_identifiers:
            swift_names = swift_names_by_type_identifier[type_identifier]
            swift_duplicates = [types for types in swift_names.values() if len(types) >= 2]

            results += swift_duplicates
        
        return results

    def _find_duplicate_objc_names(self, objc_types):
        objc_names_by_type_identifier = dict()

        type_identifiers = ObjcTypeType.ALL - {ObjcTypeType.CATEGORY, ObjcTypeType.MACRO_CONSTANT}

        for type_identifier in type_identifiers:
            objc_names_by_type_identifier[type_identifier] = dict()
        
        for objc_type in objc_types:
            name = objc_type.name
            type_identifier = objc_type.type_identifier
            if type_identifier == ObjcTypeType.MACRO_CONSTANT:
                type_identifier = ObjcTypeType.CONSTANT
            objc_names = objc_names_by_type_identifier[type_identifier]

            if name not in objc_names:
                objc_names[name] = list()
            objc_names[name].append(objc_type)
        
        # Results
        results = list()

        for type_identifier in type_identifiers:
            objc_names = objc_names_by_type_identifier[type_identifier]
            objc_duplicates = [types for types in objc_names.values() if len(types) >= 2]

            results += objc_duplicates
        
        return results

    def _find_duplicate_between_swift_and_objc(self, swift_classes, objc_classes):
        swift_names = set([c.fullname for c in swift_classes])
        objc_names = set([c.name for c in objc_classes])

        return swift_names & objc_names

    def find_duplicate_type_names(self, from_target):
        swift_types = from_target.swift_types_dependencies_filtered(type_not_in={SwiftTypeType.EXTENSION})
        objc_types = from_target.objc_types_dependencies_filtered(type_not_in={ObjcTypeType.CATEGORY})

        # Duplicates in Swift
        swift_duplicate_lists = self._find_duplicate_swift_names(swift_types)

        # Duplicates in Objective-C
        objc_duplicate_lists = self._find_duplicate_objc_names(objc_types)
        
        # Potential duplicates between Swift and Objective-C
        swift_classes = [t for t in swift_types if t.type_identifier == SwiftTypeType.CLASS]
        objc_classes = [t for t in objc_types if t.type_identifier == ObjcTypeType.CLASS]
        swift_objc_common_classes = self._find_duplicate_between_swift_and_objc(swift_classes, objc_classes)
        
        return swift_duplicate_lists, objc_duplicate_lists, swift_objc_common_classes


class SwiftFileParser():

    SWIFT_TYPE_TYPE_MAPPING = {
        'source.lang.swift.decl.protocol': SwiftTypeType.PROTOCOL,
        'source.lang.swift.decl.extension': SwiftTypeType.EXTENSION,
        'source.lang.swift.decl.struct': SwiftTypeType.STRUCT,
        'source.lang.swift.decl.enum': SwiftTypeType.ENUM,
        'source.lang.swift.decl.class': SwiftTypeType.CLASS,
    }

    def __init__(self, project_folder_path, xc_file):
        assert xc_file.is_swift

        self.project_folder_path = project_folder_path
        self.xc_file = xc_file
    
    def parse(self):
        if self.xc_file.swift_types is not None:
            return

        filepath = '{}{}'.format(self.project_folder_path, self.xc_file.filepath)
        command = ['sourcekitten', 'structure', '--file', filepath]
        result = subprocess.run(command, capture_output=True)
        swift_file_structure = json.loads(result.stdout)

        debug = False
        # debug = bool('MyTypes' in filepath)

        root_substructures = swift_file_structure.get('key.substructure', []).copy()
        swift_parser = SwiftCodeParser(substructures=root_substructures,
                                       base_discriminant=self.xc_file.filepath,
                                       type_counter=0,
                                       debug=False)
        swift_parser.parse()

        if debug:
            import pprint; pprint.pprint(swift_file_structure)

        self.xc_file.swift_types = swift_parser.swift_types

        # Set file into the type
        for swift_type in self.xc_file.swift_types:
            swift_type.file = self.xc_file
            for inner_type in swift_type.inner_types_all:
                inner_type.file = self.xc_file


class SwiftCodeParser():

    def __init__(self,
                 substructures,
                 base_discriminant,
                 type_counter,
                 debug=False):
        self.substructures = substructures
        self.base_discriminant = base_discriminant
        self.type_counter = type_counter
        self.debug = debug
    
    def parse(self):
        # import pprint; pprint.pprint(self.substructures)

        self.swift_types, self.used_types = self.parse_substructures(self.substructures)

    def parse_substructures(self, substructures):
        swift_types = list()
        used_types = set()

        substructs = substructures.copy()
        substructs.reverse()
        while substructs:
            substructure = substructs.pop()
            type_identifier = SwiftFileParser.SWIFT_TYPE_TYPE_MAPPING.get(substructure.get('key.kind'))

            if self.debug:
                print(type_identifier)

            # Type declaration
            if type_identifier:
                # We create the Swift type
                swift_type = self.parse_swift_type(substructure, type_identifier)
        
                # Add type to file
                swift_types.append(swift_type)

                # Inner types
                substructures = substructure.get('key.substructure', [])
                inner_types, used_types = self.parse_substructures(substructures)
                swift_type.inner_types += inner_types
                for inner_type in swift_type.inner_types: inner_type.parent_type = swift_type
                swift_type.used_types |= used_types

                # Then we get the following substructure and check that it is this type body.
                if substructs:
                    potential_closure = substructs.pop()

                    is_closure = False
                    
                    if potential_closure.get('key.kind') == 'source.lang.swift.expr.closure':
                        closure_substructures = potential_closure.get('key.substructure', [])
                        if closure_substructures and closure_substructures[0].get('key.kind') == 'source.lang.swift.stmt.brace':
                            body_substructures = closure_substructures[0].get('key.substructure', [])
                            if body_substructures:
                                inner_types, used_types = self.parse_substructures(body_substructures)
                                swift_type.inner_types = inner_types
                                for inner_type in swift_type.inner_types: inner_type.parent_type = swift_type
                                swift_type.used_types = used_types

                                is_closure = True
                    
                    # Was not a closure so we put it back to the substructures to manage
                    if not is_closure:
                        substructs.append(potential_closure)
            
            # Member declaration
            elif substructure.get('key.kind') == 'source.lang.swift.decl.var.local':
                type_name = substructure.get('key.typename')
                if type_name:
                    used_types.add(self.unwrapped_if_optional(type_name))
            
            # Method declaration
            elif substructure.get('key.kind') == 'source.lang.swift.decl.function.free':
                type_name = substructure.get('key.typename')
                if type_name:
                    used_types.add(self.unwrapped_if_optional(type_name))
                
                parameters = substructure.get('key.substructure', [])
                for parameter in parameters:
                    if parameter.get('key.kind') == 'source.lang.swift.decl.var.parameter':
                        used_types.add(parameter['key.typename'])
            
        return swift_types, used_types
    
    def parse_swift_type(self, substructure, type_identifier):
        # Accessibility
        if 'key.accessibility' in substructure:
            accessibility = substructure['key.accessibility'].split('.')[-1]
        else:
            accessibility = SwiftAccessibility.INTERNAL

        # Inherited types: super class and protocol conformance
        inherited_types_refs = substructure.get('key.inheritedtypes', [])
        inherited_types = {t['key.name'] for t in inherited_types_refs}

        # Type counter
        self.type_counter += 1

        # Discriminant
        discriminant = '{}_{}'.format(self.base_discriminant, self.type_counter)

        # Create Swift type
        return SwiftType(type_identifier=type_identifier,
                         name=substructure.get('key.name'),
                         accessibility=accessibility,
                         raw_inherited_types=inherited_types,
                         discriminant=discriminant)

    def parse_body_substructure(self, substructure):
        used_types = set()

        # Parse content of the type
        inner_substructures = substructure.get('key.substructure', []).copy()
        while inner_substructures:
            inner_substructure = inner_substructures.pop()

            # Types' uses
            used_types |= self.types_used_by(inner_substructure)

            # Substructures of inner substructure
            inner_substructures += inner_substructure.get('key.substructure', []).copy()
        
        return used_types

    def types_used_by(self, substructure):
        results = set()

        # Inheritance of types
        if "key.inheritedtypes" in substructure:
            inheritedtypes = substructure["key.inheritedtypes"]
            for inheritedtype in inheritedtypes:
                results.add(inheritedtype["key.name"])
            
        # Member of type and optional type (`let` as `var` is managed)
        if substructure.get("key.kind", None) == "source.lang.swift.decl.var.instance":
            results.add(self.unwrapped_if_optional(substructure["key.typename"]))
        
        # Instanciation
        if substructure.get("key.kind", None) == "source.lang.swift.expr.call":
            name = substructure["key.name"]
            if name[0].isupper():
                results.add(name)

        # Return type of method
        if substructure.get("key.kind", None) == "source.lang.swift.decl.function.method.instance":
            type_name = substructure.get("key.typename", None)
            if type_name is not None:
                results.add(self.unwrapped_if_optional(type_name))

        return results

    def unwrapped_if_optional(self, typename):
        if typename.endswith('?'):
            return typename[:-1]
        else:
            return typename


class ObjcFileParser():

    def __init__(self, xc_project, xc_file):
        assert xc_file.is_objc

        self.xc_project = xc_project
        self.xc_file = xc_file
    
    def parse(self):
        if self.xc_file.objc_types is not None or self.xc_file.objc_types is not None:
            return
        
        self.xc_file.objc_types = list()
        self.xc_file.objc_interfaces = list()
        
        xc_filepath = self.xc_project.relative_path_for_file(self.xc_file)

        with open(xc_filepath) as opened_file:
            enum_has_started = False

            for line in opened_file:
                # Objc interface
                for match in re.finditer(r'@interface\s+(\w+)\s*:\s*(\w+)', line):
                    class_name = match.group(1)
                    super_class_name = match.group(2)

                    # Add class in objective-C types of the file
                    objc_interface = ObjcInterface(class_name=class_name, super_class_name=super_class_name)
                    self.xc_file.objc_interfaces.append(objc_interface)

                # Objc class
                for match in re.finditer(r'@implementation\s+(\w+)\s*(\{)?\s*$', line):
                    class_name = match.group(1)

                    # Add class in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.CLASS, name=class_name)
                    self.xc_file.objc_types.append(objc_type)

                # Objc category
                for match in re.finditer(r'@implementation\s+(\w+)\s+\((\w*)\)', line):
                    class_name = match.group(1)
                    category_name = match.group(2)

                    # Add category in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.CATEGORY, name=class_name, category_name=category_name)
                    self.xc_file.objc_types.append(objc_type)
                
                # Objc enum
                for enum_type in ObjcEnumType.ALL:
                    regex = r'typedef ' + enum_type + r'\(\w+, (\w+)\)( \{)?'
                    for match in re.finditer(regex, line):
                        enum_name = match.group(1)

                        # Add enum in objective-C types of the file
                        objc_type = ObjcType(type_identifier=ObjcTypeType.ENUM, name=enum_name)
                        self.xc_file.objc_types.append(objc_type)
                
                # Objc 'enum'
                if xc_filepath.endswith('MyObjcClass.h'):
                    if enum_has_started:
                        for match in re.finditer(r'} (\w+);', line):
                            enum_name = match.group(1)

                            # Add enum in objective-C types of the file
                            objc_type = ObjcType(type_identifier=ObjcTypeType.ENUM, name=enum_name)
                            self.xc_file.objc_types.append(objc_type)

                            enum_has_started = False
                            break
                    elif re.findall(r'typedef enum .* \{', line):
                        enum_has_started = True
                        continue
                
                # Objc constant macro
                for match in re.finditer(r'#define (\w+) +', line):
                    constant_name = match.group(1)

                    # Add enum in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.MACRO_CONSTANT, name=constant_name)
                    self.xc_file.objc_types.append(objc_type)
                
                # Objc constant
                for match in re.finditer(r'\* ?const +(\w+)', line):
                    constant_name = match.group(1)

                    # Add enum in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.CONSTANT, name=constant_name)
                    self.xc_file.objc_types.append(objc_type)
                
                # Objc protocol
                for match in re.finditer(r'@protocol (\w+) *[^\w; ].*', line):
                    protocol_name = match.group(1)

                    # Add enum in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.PROTOCOL, name=protocol_name)
                    self.xc_file.objc_types.append(objc_type)

        # Set definition type of the type
        for objc_type in self.xc_file.objc_types:
            objc_type.file = self.xc_file


class TypeOccurrencesFromFile():

    def __init__(self,
                 swift_or_objc_type,
                 source_files_that_use,
                 occurrences_count_in_definition_file):
        self.swift_or_objc_type = swift_or_objc_type
        self.source_files_that_use = source_files_that_use
        self.occurrences_count_in_definition_file = occurrences_count_in_definition_file
    
    @property
    def inside_count(self):
        return self.occurrences_count_in_definition_file

    @property
    def outside_count(self):
        return len(self.source_files_that_use)

    @property
    def total_count(self):
        return self.inside_count + self.outside_count


class TypeOccurrencesFromType():

    def __init__(self,
                 swift_or_objc_type,
                 swift_objc_types_that_use,
                 occurrences_count_in_type_body,
                 files_that_use):
        self.swift_or_objc_type = swift_or_objc_type
        self.swift_objc_types_that_use = swift_objc_types_that_use
        self.occurrences_count_in_type_body = occurrences_count_in_type_body
        self.files_that_use = files_that_use
    
    def __repr__(self):
        types_message = ', '.join([t.name for t in self.swift_objc_types_that_use])
        files_message = ', '.join([f.filename for f in self.files_that_use])

        message_format = '{} used in: {} [occurrences in body: {} | files that use: {}]'
        return message_format.format(self.swift_or_objc_type.name,
                                     types_message,
                                     self.occurrences_count_in_type_body,
                                    files_message)
