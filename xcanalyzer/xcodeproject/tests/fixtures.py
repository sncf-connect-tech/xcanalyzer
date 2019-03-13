import os

from ..models import XcTarget, XcProject


# Models

class XcTargetFixture():

    def any_target(self, target_type=XcTarget.Type.UI_TEST):
        return XcTarget(name="MyXcTarget", target_type=target_type)


# Xcode sample project

class SampleXcodeProjectFixture():

    @property
    def root_path(self):
        """ Absolute path of this project root folder. """
        result = __file__

        for i in range(0, 4):
            result = os.path.dirname(result)
        
        return result

    @property
    def project_folder_path(self):
        """ Absolute path of the folder containing `.xcodeproj` of the Xcode project sample contained in this project. """
        return os.path.join(self.root_path, 'SampleiOSApp')

        