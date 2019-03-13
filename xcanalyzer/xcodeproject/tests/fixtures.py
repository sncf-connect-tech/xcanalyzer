from ..models import XcTarget, XcProject


class XcTargetFixture():

    def any_target(self, target_type=XcTarget.Type.UI_TEST):
        return XcTarget(name="MyXcTarget", target_type=target_type)