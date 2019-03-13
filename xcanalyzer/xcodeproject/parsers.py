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

        # Tests, extensions and app modules
        self._find_modules()

    def _check_folder_path(self):
        if not os.path.isdir(self.project_folder_path):
            raise XcodeProjectReadException("Folder not found: {}".format(self.project_folder_path))

    def _find_xcodeproj(self):
        files = os.listdir(self.project_folder_path)
        
        for filename in files:
            if filename.endswith('xcodeproj'):
                return filename
        
        raise XcodeProjectReadException("No '.xcodeproj' folder found in folder: {}".format(self.project_folder_path))

    def _find_modules(self):
        targets = self.xcode_project.objects.get_targets()

        xcode_targets = set()

        target_dependencies_names = dict()

        for target in targets:
            # Test modules
            if target.productType == 'com.apple.product-type.bundle.unit-test':
                xcode_target_type = XcTarget.Type.TEST
            
            elif target.productType == 'com.apple.product-type.bundle.ui-testing':
                xcode_target_type = XcTarget.Type.UI_TEST
            
            elif target.productType == 'com.apple.product-type.framework':
                xcode_target_type = XcTarget.Type.FRAMEWORK
            
            elif target.productType.startswith('com.apple.product-type.app-extension') \
                or target.productType == 'com.apple.product-type.watchkit2-extension':
                xcode_target_type = XcTarget.Type.EXTENSION
            
            elif target.productType.startswith('com.apple.product-type.application'):
                xcode_target_type = XcTarget.Type.APPLICATION

            # Transform into XcTarget
            xcode_target = XcTarget(target.name, xcode_target_type)
            xcode_targets.add(xcode_target)

            # Find target's dependencies
            dependencies_names = set()
            pbxproj_dependencies = [self.xcode_project.get_object(dep_key) for dep_key in target.dependencies]
            dependencies_names = [self.xcode_project.get_object(dep.target).name for dep in pbxproj_dependencies]
            target_dependencies_names[target.name] = dependencies_names

        # Set dependencies for each target        
        for target_name, dependencies_names in target_dependencies_names.items():
            target = [t for t in xcode_targets if t.name == target_name][0]
            dependencies_targets = {t for t in xcode_targets if t.name in dependencies_names}

            target.dependencies = dependencies_targets

        # Instantiate Xcode project
        self.xcode_project = XcProject(self.xcode_proj_name, targets=xcode_targets)
