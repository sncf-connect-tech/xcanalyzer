import os

from pbxproj import XcodeProject

from .exceptions import XcodeProjectReadException
from .models import XcTarget, XcProject


class XcProjectParser():

    def __init__(self, project_folder_path):
        self.project_folder_path = project_folder_path

        self.xcode_proj_name = None
        self.xcode_project = None

    def load(self):
        # Check given path
        self._check_folder_path()

        # Find xcode proj folder
        self.xcode_proj_name = self._find_xcodeproj()

        # Load pbxproj
        pbxproj_path = '{}/{}/project.pbxproj'.format(self.project_folder_path, self.xcode_proj_name)
        self.xcode_project = XcodeProject.load(pbxproj_path)

        self._find_filepaths()

        # Tests, extensions and app modules
        self._find_targets()

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

    def _find_filepaths(self):
        project_object = self.xcode_project.get_object(self.xcode_project.rootObject)
        assert project_object.isa == 'PBXProject'
        
        main_group = self.xcode_project.get_object(project_object.mainGroup)
        assert main_group.isa == 'PBXGroup'

        self.filepaths = dict()
        children_paths = [(c, '') for c in main_group.children]

        while children_paths:
            child_key, parent_path = children_paths.pop()
            child = self.xcode_project.get_object(child_key)

            if child.isa == 'PBXGroup':  # Child is a group
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

    def _find_targets(self):
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

        # Set dependencies for each target        
        for target_name, dependencies_names in target_dependencies_names.items():
            target = [t for t in xcode_targets if t.name == target_name][0]
            dependencies_targets = {t for t in xcode_targets if t.name in dependencies_names}

            target.dependencies = dependencies_targets

        # Instantiate Xcode project
        self.xcode_project = XcProject(self.xcode_proj_name, targets=xcode_targets)
