import time
import random
import math

import treedict

from toolbox import gfx
import pydyn.dynamixel as dyn

from vreptracker import VRepTracker


defaultcfg = treedict.TreeDict()

defaultcfg.objectname = 'cube'
defaultcfg.objectname_desc = 'Name of object to be tracked in the simulation'

obj_init = (+0.0045, +0.0820, +1.4798)

def distance(a, b):
    return math.sqrt(sum((a_i-b_i)*(a_i-b_i) for a_i, b_i in zip(a, b)))


class VRepSim(object):

    def __init__(self, cfg, timefactor = 1, **kwargs):
        dyn.enable_vrep()

        self.cfg = cfg
        self.cfg.update(defaultcfg, overwrite = False)

        self.ctrl = dyn.create_controller(verbose = True, motor_range = [0, 7])
        self.vt = VRepTracker(self.ctrl.io.sim, self.cfg.objectname)
        self.vt.start()

        self.dim = len(self.ctrl.motors)

        self.m_feats  = tuple(range(-2*self.dim - 1, 0))
        self.m_bounds = ((-100.0, 100.0),)*(self.dim - 1) + ((-60.0, 60.0),)
        self.m_bounds = self.m_bounds*2 + ((0.0, 300.0),)

        self.s_feats  = tuple(range(4))
        self.s_bounds = ((-3.0, 3.0), (-3.0, 3.0), (1.4, 1.6), (0.0, 1.0))

        self.timefactor = timefactor

    @property
    def _arm_pos(self):
        return (m.position-150.0 for m in self.ctrl.motors)

    def wait(self, target_pose, dur):
        start = time.time()
        stability = 0
        last_pose = target_pose
        while time.time() - start < dur-0.1:
            pose = self._arm_pos
            if all(abs(ap_i - p_i) < 0.5 for ap_i, p_i in zip(pose, target_pose)):
                time.sleep(0.05)
                return True
            # else:
            #     if all(abs(p1_i - p2_i) < 0.001 and p1_i != p2_i for ap_i, p_i in zip(pose, last_pose)):
            #         stability += 1
            #     else:
            #         stability = 0
            #         last_pose = pose
            # if stability > 5:
            #     return False
            time.sleep(0.01)

        time.sleep(0.05)
        return False

    def execute_order(self, order, **kwargs):
        assert len(order) == len(self.m_feats)

        pose0 = order[0:self.dim]
        pose1 = order[self.dim:2*self.dim]
        maxspeed = order[2*self.dim]

        self.ctrl.stop_sim()
        time.sleep(0.1)

        self.ctrl.start_sim()
        time.sleep(0.1)

        if not all(abs(ap_i) < 1.0 for ap_i in self._arm_pos):
            time.sleep(0.5)
            self.ctrl.stop_sim()
            time.sleep(0.5)

            self.ctrl.start_sim()
            time.sleep(0.5)

        assert all(abs(ap_i) < 1.0 for ap_i in self._arm_pos)

        pose = self.vt.pose[0:3] # crucial ! refresh the registering
        for p_i, m in zip(pose0, self.ctrl.motors):
            m.speed = maxspeed
            m.position = p_i + 150.0

        time.sleep(self.timefactor*0.25)
#        self.wait(pose0, 0.5)

        for p_i, m in zip(pose1, self.ctrl.motors):
            m.position = p_i + 150.0

        time.sleep(self.timefactor*0.25)
#        self.wait(pose1, 0.5)
        #print max(abs(m.position-p_i-150.0) for m, p_i in zip(self.ctrl.motors, pose1))
        pose = self.vt.pose[0:3]

        if distance(obj_init, pose) > 0.01:
            effect = tuple(pose) + (1.0,)
        else:
            effect = tuple(pose) + (0.0,)

        if self.cfg.verbose or self.cfg.inner_verbose:
            color = gfx.green if effect[3] == 1.0 else gfx.red
            print('{} -> {}{}{}'.format(gfx.ppv(order, fmt='+7.2f'), color, gfx.ppv(effect, fmt='+7.4f'), gfx.end))

        return effect

    def close(self):
        self.ctrl.stop_sim()
        self.vt.close()