import os

import openstep_parser as osp
from pbxproj import XcodeProject

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
        self.object = XcProject(self.project_folder_path,
                                xcode_proj_name,
                                targets=set(),
                                groups=list(),
                                files=root_files)

        # Groups
        if self.verbose:
            print("-> Parse groups")
        self.object.groups = self._parse_groups()

        # Tests, extensions and app modules
        if self.verbose:
            print("-> Parse targets")
        self.object.targets = self._parse_targets()

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
