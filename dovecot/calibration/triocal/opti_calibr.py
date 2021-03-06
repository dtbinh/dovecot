from __future__ import print_function, division, absolute_import
import time
import sys

import numpy as np


from environments import tools
from ...ext.toolbox import gfx
from ...ext import natnet

from ...stemsim import stemcom
from ...vrepsim import sim_env
from ... import prims
from ...cfgdesc import desc, objdesc

def Rot(M33):
    R = np.eye(4)
    for i in range(3):
        for j in range(3):
            R[i, j] = M33[i, j]
    return np.matrix(R)

def Trans(T3):
    T = np.eye(4)
    for i in range(3):
        T[i, 3] = T3[i]
    return np.matrix(T)

def Scale(factor):
    S = np.eye(4)
    for i in range(3):
        S[i, i] = factor
    return np.matrix(S)

def transform_3D(A, B, scaling=True):
    assert A.shape == B.shape

    # originize A and B
    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)

    A_c = A - np.tile(centroid_A, (A.shape[0], 1))
    B_c = B - np.tile(centroid_B, (B.shape[0], 1))

    # detect scaling
    norm_A = np.linalg.norm(A_c)
    norm_B = np.linalg.norm(B_c)
    if norm_B != 0:
        scaling_AB = norm_A/norm_B

    A_u = A_c/scaling_AB

    # A and B are only a rotation away now !
    H = np.transpose(A_u) * B_c
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T * U.T

    # if reflection case
    if np.linalg.det(R) < 0:
       Vt[2,:] *= -1
       R = Vt.T * U.T

    return Trans(centroid_B.T)*Rot(R)*Scale(1.0/scaling_AB)*Trans(-centroid_A.T)

def vrep_capture(poses):

    cfg = desc._deepcopy()

    cfg.execute.is_simulation         = True
    cfg.execute.prefilter             = False
    cfg.execute.check_self_collisions = False

    cfg.execute.scene.name        = 'vanilla'
    cfg.execute.scene.objects.ball45 = objdesc._deepcopy()
    cfg.execute.scene.objects.ball45.pos     = (None, None, None)
    cfg.execute.scene.objects.ball45.mass    = -1
    cfg.execute.scene.objects.ball45.tracked = True

    cfg.execute.simu.ppf        = 200
    cfg.execute.simu.mac_folder = '/Applications/V-REP/v_rep/bin'
    cfg.execute.simu.load       = True
    cfg.execute.simu.headless   = True
    cfg.execute.simu.calibrdir  = '~/.dovecot/tttcal/'

    cfg.sprims.names      = ['push']
    cfg.sprims.uniformize = False
    cfg.sprims.tip        = True

    cfg.mprims.dt           = 0.01
    cfg.mprims.name         = 'dmp_sharedwidth'
    cfg.mprims.target_end   =  500
    cfg.mprims.traj_end     = 1500
    cfg.mprims.sim_end      = 1500
    cfg.mprims.uniformize   = False
    cfg.mprims.n_basis      = 2
    cfg.mprims.max_speed    = 30.0

    cfg.mprims.init_states   = [-30.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    cfg.mprims.target_states = [  0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    cfg.mprims.angle_ranges  = ((110.0,  110.0), (99.0, 99.0), (99.0, 99.0), (120.0, 120.0), (99.0, 99.0), (99.0, 99.0))

    sb = sim_env.SimulationEnvironment(cfg)

    vrep_res = []
    for tg in poses:
        cfg.mprims.target_states = tg
        print(tg)
        sb.m_prim = prims.create_mprim(cfg.mprims.name, cfg)

        m_signal = tools.to_signal((0.0, 0.0)*cfg.mprims.n_basis*6 + (0.20, 0.20),
                                   sb.m_channels)
        meta = {}
        sb.execute(m_signal, meta=meta)
        vrep_res.append(np.mean([meta['log']['raw_sensors']['tip_pos'][-50:]], axis=1))

    sb.close()
    return vrep_res

def opti_capture(poses, stemcfg, fb=None):
    cfg = desc._deepcopy()
    cfg.execute.hard.uid = stemcfg.uid
    stem_com = stemcom.StemCom(cfg)

    stem_com.ms.moving_speed    = 100
    stem_com.ms.torque_limit = stemcfg.max_torque

    time.sleep(0.1)

    stem_com.setup(poses[0])

    reached = []
    mean_p  = []
    for pose in poses:
        print(pose)
        err_array = stem_com.go_to(pose, margin=1.0, timeout=4.0)

        if len(pose) < 7 or pose[6]:
            reached.append(np.array(pose)+np.array(err_array))
            print("err: {}".format(gfx.ppv(err_array)))

            fb = natnet.FrameBuffer(4.0, addr=stemcfg.optitrack_addr)
            time.sleep(0.1)
            assert fb.fps > 100.0
            fb.track(stemcfg.optitrack_side)
            start = time.time()
            time.sleep(1.0)
            end   = time.time()
            fb.stop_tracking()
            pdata = fb.tracking_slice(start, end)
            fb.stop()
            fb.join()
            m = np.mean([p[1] for p in pdata], axis=0)
            print(np.std([p[1] for p in pdata], axis=0))
            if len(mean_p) > 0:
                if np.linalg.norm(m - mean_p[-1]) < 0.05:
                    print("{}error{}: the stem is not moving enough, is it the right marker ?".format(gfx.bred, gfx.end))
                    stem_com.rest()
                    time.sleep(1.0)
                    sys.exit(1)
            mean_p.append(m)


    stem_com.rest()

    return reached, mean_p

def compute_calibration(opti_res, vrep_res):

    assert len(opti_res) == len(vrep_res)
    n = len(opti_res)
    print(np.mat(opti_res))
    print(np.mat(vrep_res))
    Mtrans = transform_3D(np.mat(opti_res), np.mat(vrep_res))

    Mtrio = np.hstack((np.matrix(opti_res), np.ones(shape=(n, 1))))
    Mvrep = np.hstack((np.matrix(vrep_res), np.ones(shape=(n, 1))))

    Mvrep2 = (Mtrans*Mtrio.T).T

    err = Mvrep2 - Mvrep
    err = np.sum(np.multiply(err, err))
    rmse = np.sqrt(err/n)
    print(rmse)

    print(Mtrans)
    #self.assertTrue(rmse < 1e-10)
    return Mtrans
