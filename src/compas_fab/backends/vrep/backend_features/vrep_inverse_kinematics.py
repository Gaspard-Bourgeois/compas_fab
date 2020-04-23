from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fab.backends.vrep.helpers import assert_robot, frame_to_vrep_pose, config_from_vrep


class VrepInverseKinematics(object):
    def __init__(self, client):
        self.client = client

    def __call__(self, robot, goal_frame, metric_values=None, gantry_joint_limits=None, arm_joint_limits=None, max_trials=None, max_results=1):
        return self.inverse_kinematics(robot, goal_frame, metric_values, gantry_joint_limits, arm_joint_limits, max_trials, max_results)

    def inverse_kinematics(self, robot, goal_frame, metric_values=None, gantry_joint_limits=None, arm_joint_limits=None, max_trials=None, max_results=1):
        """Calculates inverse kinematics to find valid robot configurations for the specified goal frame.

        Args:
            robot (:class:`compas_fab.robots.Robot`): Robot instance.
            goal_frame (:class:`Frame`): Target or goal frame.
            metric_values (:obj:`list` of :obj:`float`): List containing one value
                per configurable joint. Each value ranges from 0 to 1,
                where 1 indicates the axis/joint is blocked and cannot
                move during inverse kinematic solving.
            gantry_joint_limits (:obj:`list` of `float`): List of 6 floats defining the upper/lower limits of
                gantry joints. Use this if you want to restrict the area in which to search for states.
            arm_joint_limits (:obj:`list` of `float`): List of 12 floats defining the upper/lower limits of
                arm joints. Use this if you want to restrict the working area in which to search for states.
            max_trials (:obj:`int`): Number of trials to run. Set to ``None``
                to retry infinitely.
            max_results (:obj:`int`): Maximum number of result states to return.

        Returns:
            list: List of :class:`Configuration` objects representing
            the collision-free configuration for the ``goal_frame``.
        """
        assert_robot(robot)

        joints = len(robot.get_configurable_joints())
        if not metric_values:
            metric_values = [0.1] * joints

        self.client.set_robot_metric(robot, metric_values)

        states = self.client.find_raw_robot_states(robot, frame_to_vrep_pose(goal_frame, self.client.scale), gantry_joint_limits, arm_joint_limits, max_trials, max_results)

        return [config_from_vrep(states[i:i + joints], self.client.scale)
                for i in range(0, len(states), joints)]
