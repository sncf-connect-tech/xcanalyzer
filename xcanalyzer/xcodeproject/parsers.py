import os

import openstep_parser as osp
from pbxproj import XcodeProject

from .exceptions import XcodeProjectReadException
from .models import XcTarget, XcProject, XcGroup, XcFile


class XcProjectParser():

    def __init__(self, project_folder_path):
        self.project_folder_path = project_folder_path

    def load(self):
        # Check given path
        self._check_folder_path()

        # Find xcode proj folder
        xcode_proj_name = self._find_xcodeproj()

        # Load pbxproj
        pbxproj_path = '{}/{}/project.pbxproj'.format(self.project_folder_path, xcode_proj_name)

        with open(pbxproj_path, 'r') as f:  # To avoid ResourceWarning: unclosed file
            tree = osp.OpenStepDecoder.ParseFromFile(f)
            self.xcode_project = XcodeProject(tree, pbxproj_path)

        # Files a project root
        root_files = self._find_root_files()

        # Output object
        self.object = XcProject(xcode_proj_name, targets=set(), groups=set(), files=root_files)

        # Groups
        self.object.groups = self._parse_groups()

        self._find_filepaths()

        # Tests, extensions and app modules
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

    def _file_name_for_file_ref(self, file_ref):
        assert file_ref.isa == 'PBXFileReference'

        if file_ref.sourceTree == '<group>':  # Relative to group
            return file_ref.path
    
        elif file_ref.sourceTree == 'SOURCE_ROOT':  # Relative to project
            return file_ref.path

    def _find_root_files(self):
        results = set()

        for child_key in self._main_group.children:
            child = self.xcode_project.get_object(child_key)
            if child.isa == 'PBXFileReference':
                filename = self._file_name_for_file_ref(child)
                results.add(XcFile(filename))

        return results

    def _parse_groups(self):
        # key is a child key reference, value is the XcGroup destination of the group's parent
        children_to_treat = dict()

        root_group = XcGroup('root')
        for child_key in self._main_group.children:
            child = self.xcode_project.get_object(child_key)
            if child.isa != 'PBXGroup':
                continue
            children_to_treat[child_key] = root_group

        while children_to_treat:
            current_child_key = list(children_to_treat.keys())[0]
            parent_group = children_to_treat.pop(current_child_key)
            current_child = self.xcode_project.get_object(current_child_key)
            if current_child.isa != 'PBXGroup':
                continue
            
            # Current child name
            if hasattr(current_child, 'name'):
                name = current_child.name
            else:
                name = current_child.path

            # Link the parent with its child
            current_group = XcGroup(name)
            parent_group.groups.add(current_group)

            # Add this child's children for treatment
            for child_key in current_child.children:
                children_to_treat[child_key] = current_group
        
        return root_group.groups

    def _find_filepaths(self):
        self.filepaths = dict()
        children_paths = [(c, '') for c in self._main_group.children]

        while children_paths:
            child_key, parent_path = children_paths.pop()
            child = self.xcode_project.get_object(child_key)

            if child.isa in {'PBXGroup', 'PBXVariantGroup'}:  # Child is a group
                if hasattr(child, 'path'):
                    if child.sourceTree == '<group>':  # Relative to group
                        child_path = '/'.join([parent_path, child.path])
                
                    elif child.sourceTree == 'SOURCE_ROOT':  # Relative to project
                        child_path = '/{}'.format(child.path)
                else:
                    child_path = parent_path

                # Add children to compute paths in next steps
                for grandchild in child.children:
                    children_paths.append((grandchild, child_path))
            
            elif child.isa == 'PBXFileReference':  # Child is file reference
                if child.sourceTree == '<group>':  # Relative to group
                    self.filepaths[child] = '/'.join([parent_path, child.path])
            
                elif child.sourceTree == 'SOURCE_ROOT':  # Relative to project
                    self.filepaths[child] = '/{}'.format(child.path)

    def _parse_targets(self):
        targets = self.xcode_project.objects.get_targets()

        xcode_targets = set()

        target_dependencies_names = dict()

        for target in targets:
            # Test modules
            xcode_target_type = self._map_target_type(target)

            # Transform into XcTarget
            xcode_target = XcTarget(target.name,
                                    xcode_target_type,
                                    dependencies=set(),
                                    source_files=set())
            xcode_targets.add(xcode_target)

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
                        xcode_target.source_files.add(self.filepaths[file_ref])

                # Resources files
                elif build_phase.isa == 'PBXResourcesBuildPhase':
                    for build_file_key in build_phase.files:
                        build_file = self.xcode_project.get_object(build_file_key)
                        file_ref = self.xcode_project.get_object(build_file.fileRef)

                        if file_ref.isa == 'PBXVariantGroup':  # Localized resource files
                            for child in file_ref.children:
                                variant_file_ref = self.xcode_project.get_object(child)
                                xcode_target.resource_files.add(self.filepaths[variant_file_ref])
                        else:
                            xcode_target.resource_files.add(self.filepaths[file_ref])

        # Set dependencies for each target        
        for target_name, dependencies_names in target_dependencies_names.items():
            target = [t for t in xcode_targets if t.name == target_name][0]
            dependencies_targets = {t for t in xcode_targets if t.name in dependencies_names}

            target.dependencies = dependencies_targets
    
        return xcode_targets
