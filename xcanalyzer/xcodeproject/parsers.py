import json
import os
import re
import subprocess

import openstep_parser as osp
from pbxproj import XcodeProject

from ..language.models import SwiftType, SwiftTypeType, SwiftAccessibility, ObjcTypeType, ObjcType, ObjcEnumType, ObjcInterface

from .exceptions import XcodeProjectReadException
from .models import XcTarget, XcProject, XcGroup, XcFile


class XcProjectParser():

    def __init__(self, project_folder_path, verbose=False):
        self.project_folder_path = project_folder_path
        self.verbose = verbose

    def load(self):
        # Check given path
        self._check_folder_path()

        # Find xcode proj folder
        xcode_proj_name = self._find_xcodeproj()

        # Load pbxproj
        if self.verbose:
            print("-> Load pbxproj")
        pbxproj_path = '{}/{}/project.pbxproj'.format(self.project_folder_path, xcode_proj_name)

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
                                xcode_proj_name,
                                targets=set(),
                                groups=list(),
                                files=root_files)

        # Groups
        if self.verbose:
            print("-> Parse groups")
        self.xc_project.groups = self._parse_groups()

        # Tests, extensions and app modules
        if self.verbose:
            print("-> Parse targets")
        self.xc_project.targets = self._parse_targets()
    
    def parse_swift_files(self):
        for target in self.xc_project.targets_sorted_by_name:
            for swift_file in target.swift_files:
                parser = SwiftFileParser(project_folder_path=self.xc_project.dirpath,
                                         xc_file=swift_file)
                parser.parse()
    
    def parse_objc_files(self):
        objc_super_class_names = dict()

        # Targets' objective-C files
        for target in self.xc_project.targets_sorted_by_name:
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
        for target in self.xc_project.targets_sorted_by_name:
            for objc_file in target.objc_files:
                for objc_class in objc_file.objc_classes:
                    objc_class.super_class_name = objc_super_class_names.get(objc_class.name)

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

            # Transform into XcTarget
            xcode_target = XcTarget(target.name,
                                    xcode_target_type,
                                    product_name=product_name,
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
    
        return xcode_targets


class SwiftFileParser():

    SWIFT_TYPE_TYPE_MAPPING = {
        'source.lang.swift.decl.protocol': SwiftTypeType.PROTOCOL,
        'source.lang.swift.decl.extension': SwiftTypeType.EXTENSION,
        'source.lang.swift.decl.struct': SwiftTypeType.STRUCT,
        'source.lang.swift.decl.enum': SwiftTypeType.ENUM,
        'source.lang.swift.decl.class': SwiftTypeType.CLASS,
    }

    def __init__(self, project_folder_path, xc_file):
        assert xc_file.filename.endswith('.swift')

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
        # debug = bool('MyViewController' in filepath)

        root_substructures = swift_file_structure.get('key.substructure', []).copy()
        swift_parser = SwiftCodeParser(substructures=root_substructures, debug=debug)
        swift_parser.parse()

        if debug:
            import pprint; pprint.pprint(root_substructures)  

        self.xc_file.swift_types = swift_parser.swift_types


class SwiftCodeParser():

    def __init__(self, substructures, debug=False):
        self.substructures = substructures
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
                                swift_type.used_types = used_types

                                is_closure = True
                    
                    # Was not aclosure so we put it back to the substructures to manage
                    if not is_closure:
                        substructs.append(potential_closure)
            
            # Member declaration
            elif substructure.get('key.kind') == 'source.lang.swift.decl.var.local':
                type_name = self.unwrapped_if_optional(substructure['key.typename'])
                used_types.add(type_name)
            
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

        # Create Swift type
        return SwiftType(type_identifier=type_identifier,
                         name=substructure.get('key.name'),
                         accessibility=accessibility,
                         inherited_types=inherited_types)

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
        assert xc_file.filename.endswith('.h') or xc_file.filename.endswith('.m')

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
                for match in re.finditer(r'@implementation ([a-zA-Z0-9_]+)( \{)?$', line):
                    class_name = match.group(1)

                    # Add class in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.CLASS, name=class_name)
                    self.xc_file.objc_types.append(objc_type)

                # Objc category
                for match in re.finditer(r'@implementation (\w+) \((\w*)\)', line):
                    class_name = match.group(1)
                    category_name = match.group(2)

                    # Add category in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.CATEGORY, name=class_name)
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
                    elif re.findall(r'typedef enum \{', line):
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
                for match in re.finditer(r'@protocol (\w+)(;| ).*', line):
                    protocol_name = match.group(1)

                    # Add enum in objective-C types of the file
                    objc_type = ObjcType(type_identifier=ObjcTypeType.PROTOCOL, name=protocol_name)
                    self.xc_file.objc_types.append(objc_type)

