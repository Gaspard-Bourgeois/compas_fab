from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from timeit import default_timer as timer

from compas_fab.backends.vrep.helpers import assert_robot, config_to_vrep, frame_to_vrep_pose, floats_to_vrep, config_from_vrep, VrepError


class VrepPlanMotion(object):
    SUPPORTED_PLANNERS = ('bitrrt', 'bkpiece1', 'est', 'kpiece1',
                          'lazyprmstar', 'lbkpiece1', 'lbtrrt', 'pdst',
                          'prm', 'prrt', 'rrt', 'rrtconnect', 'rrtstar',
                          'sbl', 'stride', 'trrt')

    def __init__(self, client):
        self.client = client

    def __call__(self, robot, goal_frame, metric_values=None, collision_meshes=None,
                 planner_id='rrtconnect', trials=1, resolution=0.02,
                 gantry_joint_limits=None, arm_joint_limits=None, shallow_state_search=True, optimize_path_length=False,
                 log=None):
        return self.plan_motion(robot, goal_frame, metric_values, collision_meshes,
                                planner_id, trials, resolution,
                                gantry_joint_limits, arm_joint_limits, shallow_state_search, optimize_path_length,
                                log)

    def plan_motion(self, robot, goal_frame, metric_values=None, collision_meshes=None,
                    planner_id='rrtconnect', trials=1, resolution=0.02,
                    gantry_joint_limits=None, arm_joint_limits=None, shallow_state_search=True, optimize_path_length=False,
                    log=None):
        """Find a path plan to move the selected robot from its current position to the `goal_frame`.

        Args:
            robot (:class:`compas_fab.robots.Robot`): Robot instance to move.
            goal_frame (:class:`Frame`): Target or goal frame.
            metric_values (:obj:`list` of :obj:`float`): List containing one value
                per configurable joint. Each value ranges from 0 to 1,
                where 1 indicates the axis/joint is blocked and cannot
                move during inverse kinematic solving.
            collision_meshes (:obj:`list` of :class:`compas.datastructures.Mesh`): Collision meshes
                to be taken into account when calculating the motion plan.
                Defaults to ``None``.
            planner_id (:obj:`str`): Name of the planner to use. Defaults to ``rrtconnect``.
            trials (:obj:`int`): Number of search trials to run. Defaults to ``1``.
            resolution (:obj:`float`): Validity checking resolution. This value
                is specified as a fraction of the space's extent.
                Defaults to ``0.02``.
            gantry_joint_limits (:obj:`list` of `float`): List of 6 floats defining the upper/lower limits of
                gantry joints. Use this if you want to restrict the working area of the path planner.
            arm_joint_limits (:obj:`list` of `float`): List of 12 floats defining the upper/lower limits of
                arm joints. Use this if you want to restrict the working area of the path planner.
            shallow_state_search (:obj:`bool`): True to search only a minimum of
                valid states before searching a path, False to search states intensively.
            optimize_path_length (:obj:`bool`): True to search the path with minimal total length among all `trials`,
                False to return the first valid path found. It only affects the output if `trials > 1`.
            log (:class:`Logger`): Logger object to aid debugging. Default to ``None``.

        Returns:
            list: List of :class:`Configuration` objects representing the
            collision-free path to the ``goal_frame``.
        """
        assert_robot(robot)
        return self._find_path_plan(robot, {'target_type': 'pose', 'target': goal_frame},
                                    metric_values, collision_meshes, planner_id, trials, resolution,
                                    gantry_joint_limits, arm_joint_limits, shallow_state_search, optimize_path_length,
                                    log)

    def plan_motion_to_config(self, robot, goal_configs, metric_values=None, collision_meshes=None,
                              planner_id='rrtconnect', trials=1, resolution=0.02,
                              gantry_joint_limits=None, arm_joint_limits=None, shallow_state_search=True, optimize_path_length=False,
                              log=None):
        """Find a path plan to move the selected robot from its current position to one of the `goal_configs`.

        This function is useful when it is required to get a path plan that ends in one
        specific goal configuration.

        Args:
            robot (:class:`compas_fab.robots.Robot`): Robot instance to move.
            goal_configs (:obj:`list` of :class:`Configuration`): List of target or goal configurations.
            metric_values (:obj:`list` of :obj:`float`): List containing one value
                per configurable joint. Each value ranges from 0 to 1,
                where 1 indicates the axis/joint is blocked and cannot
                move during inverse kinematic solving.
            collision_meshes (:obj:`list` of :class:`compas.datastructures.Mesh`): Collision meshes
                to be taken into account when calculating the motion plan.
                Defaults to ``None``.
            planner_id (:obj:`str`): Name of the planner to use. Defaults to ``rrtconnect``.
            trials (:obj:`int`): Number of search trials to run. Defaults to ``1``.
            resolution (:obj:`float`): Validity checking resolution. This value
                is specified as a fraction of the space's extent.
                Defaults to ``0.02``.
            gantry_joint_limits (:obj:`list` of `float`): List of 6 floats defining the upper/lower limits of
                gantry joints. Use this if you want to restrict the working area of the path planner.
            arm_joint_limits (:obj:`list` of `float`): List of 12 floats defining the upper/lower limits of
                arm joints. Use this if you want to restrict the working area of the path planner.
            shallow_state_search (:obj:`bool`): True to search only a minimum of
                valid states before searching a path, False to search states intensively.
            optimize_path_length (:obj:`bool`): True to search the path with minimal total length among all `trials`,
                False to return the first valid path found. It only affects the output if `trials > 1`.
            log (:class:`Logger`): Logger object to aid debugging. Default to ``None``.

        Returns:
            list: List of :class:`Configuration` objects representing the
            collision-free path to the ``goal_configs``.
        """
        assert_robot(robot)
        return self._find_path_plan(robot, {'target_type': 'config', 'target': goal_configs},
                                    metric_values, collision_meshes, planner_id, trials, resolution,
                                    gantry_joint_limits, arm_joint_limits, shallow_state_search, optimize_path_length,
                                    log)

    def _find_path_plan(self, robot, goal, metric_values, collision_meshes,
                        planner_id, trials, resolution,
                        gantry_joint_limits, arm_joint_limits, shallow_state_search, optimize_path_length,
                        log):

        joints = len(robot.get_configurable_joints())
        if not metric_values:
            metric_values = [0.1] * joints

        if planner_id not in self.SUPPORTED_PLANNERS:
            raise ValueError('Unsupported planner_id. Must be one of: ' + str(self.SUPPORTED_PLANNERS))

        first_start = timer() if log else None
        if collision_meshes:
            self.client.add_meshes(collision_meshes)
        if log:
            log.debug('Execution time: add_meshes=%.2f', timer() - first_start)

        start = timer() if log else None
        self.client.set_robot_metric(robot, metric_values)
        if log:
            log.debug('Execution time: set_robot_metric=%.2f', timer() - start)

        if 'target_type' not in goal:
            raise ValueError('Invalid goal type, you are using an internal function but passed incorrect args')

        if goal['target_type'] == 'config':
            states = []
            for c in goal['target']:
                states.extend(config_to_vrep(c, self.client.scale))
        elif goal['target_type'] == 'pose':
            start = timer() if log else None
            max_trials = None if shallow_state_search else 80
            max_results = 1 if shallow_state_search else 80
            states = self.client.find_raw_robot_states(robot, frame_to_vrep_pose(goal['target'], self.client.scale), gantry_joint_limits, arm_joint_limits, max_trials, max_results)
            if log:
                log.debug('Execution time: search_robot_states=%.2f', timer() - start)

        start = timer() if log else None
        string_param_list = [planner_id]
        if gantry_joint_limits or arm_joint_limits:
            joint_limits = []
            joint_limits.extend(floats_to_vrep(gantry_joint_limits or [], self.client.scale))
            joint_limits.extend(arm_joint_limits or [])
            string_param_list.append(','.join(map(str, joint_limits)))

        if log:
            log.debug('About to execute path planner: planner_id=%s, trials=%d, shallow_state_search=%s, optimize_path_length=%s',
                      planner_id, trials, shallow_state_search, optimize_path_length)

        res, _, path, _, _ = self.client.run_child_script('searchRobotPath',
                                                   [robot.model.attr['index'],
                                                    trials,
                                                    (int)(resolution * 1000),
                                                    1 if optimize_path_length else 0],
                                                   states, string_param_list)
        if log:
            log.debug('Execution time: search_robot_path=%.2f', timer() - start)

        if res != 0:
            raise VrepError('Failed to search robot path', res)

        if log:
            log.debug('Execution time: total=%.2f', timer() - first_start)

        return [config_from_vrep(path[i:i + joints], self.client.scale)
                for i in range(0, len(path), joints)]
