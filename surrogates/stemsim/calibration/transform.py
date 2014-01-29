from __future__ import division, print_function
import numpy as np

def _detect_gaps(trajectory):
    assert trajectory[0] is not None
    gaps = []
    in_gap = False
    for i, t in enumerate(trajectory):
        if t is None:
            if not in_gap:
                gaps.append([i, None])
                in_gap = True
        else:
            if in_gap:
                assert gaps[-1][1] is None
                gaps[-1][1] = i-1
                in_gap = False
    return gaps

def fill_gaps(trajectory):
    gaps = _detect_gaps(trajectory)
    for start, end in gaps:
        size = end-start+1
        just_before = np.array(trajectory[start-1])
        just_after  = np.array(trajectory[end+1])
        for i, j in enumerate(range(start, end+1)):
            trajectory[j] = (just_before*(size-i) + i*just_after)/size

    assert all(t is not None for t in trajectory)
    return trajectory

def opti2vrep(opti_traj, M):
    vrep_traj = []
    for ts, opti_v in opti_traj:
        opti_u = np.matrix([list(opti_v)+[1]]).T
        vrep_u = M*opti_u
        vrep_v = (vrep_u[0, 0], vrep_u[1, 0], vrep_u[2, 0])
        vrep_traj.append((ts, vrep_v))
    return vrep_traj