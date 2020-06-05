from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fab.backends.client_interface import PlannerInterface
from compas_fab.backends.vrep.backend_features.vrep_add_attached_collision_mesh import VrepAddAttachedCollisionMesh
from compas_fab.backends.vrep.backend_features.vrep_add_collision_mesh import VrepAddCollisionMesh
from compas_fab.backends.vrep.backend_features.vrep_forward_kinematics import VrepForwardKinematics
from compas_fab.backends.vrep.backend_features.vrep_inverse_kinematics import VrepInverseKinematics
from compas_fab.backends.vrep.backend_features.vrep_plan_motion import VrepPlanMotion
from compas_fab.backends.vrep.backend_features.vrep_remove_collision_mesh import VrepRemoveCollisionMesh


class VrepPlanner(PlannerInterface):
    def __init__(self, client):
        super(VrepPlanner, self).__init__(client)
        self.forward_kinematics = VrepForwardKinematics(self.client)
        self.inverse_kinematics = VrepInverseKinematics(self.client)
        self.plan_motion = VrepPlanMotion(self.client)
        self.plan_motion_to_config = VrepPlanMotion(self.client).plan_motion_to_config
        self.add_attached_collision_mesh = VrepAddAttachedCollisionMesh(self.client)
        self.pick_building_member = VrepAddAttachedCollisionMesh(self.client).pick_building_member
        self.add_collision_mesh = VrepAddCollisionMesh(self.client)
        self.remove_collision_mesh = VrepRemoveCollisionMesh(self.client)
