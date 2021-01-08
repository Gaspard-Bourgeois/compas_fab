import compas
import Grasshopper
import System
from compas.robots import RobotModel
from compas_ghpython.artists import RobotModelArtist
from ghpythonlib.componentbase import dotnetcompiledcomponent as component
from scriptcontext import sticky as st

from compas_fab.backends import RosFileServerLoader
from compas_fab.ghpython.components import create_id
from compas_fab.ghpython.components.icons import default_icon
from compas_fab.robots import Robot
from compas_fab.robots import RobotSemantics


class ROSRobot(component):
    def __new__(cls):
        return Grasshopper.Kernel.GH_Component.__new__(cls,
                                                       "ROS Robot",
                                                       "ROS Robot",
                                                       """Load robot directly from ROS.""",
                                                       "COMPAS FAB",
                                                       "ROS")

    def get_ComponentGuid(self):
        return System.Guid("2c99e9cb-441c-4c9f-9d7a-593536c1e0da")

    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True

    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "ros_client", "ros_client", ":class:`compas_fab.backends.RosClient` The ROS client.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "load", "load", "If `True`, loads the robot from ROS. Defaults to False.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "robot", "robot", "The robot.")
        self.Params.Output.Add(p)

    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        result = self.RunScript(p0, p1)

        if result is not None:
            self.marshal.SetOutput(result, DA, 0, True)

    def get_Internal_Icon_24x24(self):
        return default_icon

    def RunScript(self, ros_client, load):
        compas.PRECISION = '24f'
        key = create_id(self, 'robot')

        if ros_client and ros_client.is_connected and load:
            # Load URDF from ROS
            loader = RosFileServerLoader(ros_client)
            urdf = loader.load_urdf()
            srdf = loader.load_srdf()

            # Create robot model from URDF and load geometry
            model = RobotModel.from_urdf_string(urdf)
            model.load_geometry(loader)
            semantics = RobotSemantics.from_srdf_string(srdf, model)
            robot = Robot(model, semantics=semantics)
            robot.artist = RobotModelArtist(robot.model)
            st[key] = robot

        robot = st.get(key, None)
        if robot:  # client sometimes need to be restarted, without needing to reload geometry
            robot.client = ros_client
        return robot