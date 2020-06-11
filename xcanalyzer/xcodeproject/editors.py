import os

import openstep_parser as osp
from pbxproj import XcodeProject



class XcodeProjectEditor():

    def __init__(self, project_folder_path):
        self.project_folder_path = project_folder_path

        self.load()
    
    def load(self):
        # Check given path
        self._check_folder_path()

        # Find xcode proj folder
        self.xcode_proj_name = self._find_xcodeproj()

        # Load pbxproj
        pbxproj_path = '{}/{}/project.pbxproj'.format(self.project_folder_path, self.xcode_proj_name)

        # Open pbxproj
        with open(pbxproj_path, 'r') as f:  # To avoid ResourceWarning: unclosed file
            tree = osp.OpenStepDecoder.ParseFromFile(f)
            self.xcode_project = XcodeProject(tree, pbxproj_path)

    def _check_folder_path(self):
        if not os.path.isdir(self.project_folder_path):
            raise XcodeProjectReadException("Folder not found: {}".format(self.project_folder_path))

    def _find_xcodeproj(self):
        files = os.listdir(self.project_folder_path)
        
        for filename in files:
            if filename.endswith('xcodeproj'):
                return filename
        
        raise XcodeProjectReadException("No '.xcodeproj' folder found in folder: {}".format(self.project_folder_path))
    
    def save(self):
        self.xcode_project.save()

    def set_project_build_setting(self, build_setting_key, build_setting_value):
        project = self.xcode_project.get_object(self.xcode_project.rootObject)

        build_configurations_list = self.xcode_project.get_object(project.buildConfigurationList)
        for build_configuration_key in build_configurations_list.buildConfigurations:
            build_configuration = self.xcode_project.get_object(build_configuration_key)  # .buildSettings
            build_configuration.set_flags(build_setting_key, build_setting_value)
    
    def delete_target_build_setting(self, build_setting_key, target_name):
        self.xcode_project.remove_flags(build_setting_key, None, target_name=target_name)
