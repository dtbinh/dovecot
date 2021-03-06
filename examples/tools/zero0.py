from __future__ import division, print_function
import sys
import time

from dovecot.ext.pydyn import MotorSet
import dotdot
import dotdot
import dovecot
from dovecot.ext import powerswitch
from dovecot.stemsim import stemcfg

if len(sys.argv) >= 2:
    uid = int(sys.argv[1])
else:
    uid = dovecot.stem_uid()

stem = stemcfg.stems[uid]
stem.cycle_usb()

ms = MotorSet(serial_id=stem.serial_id, motor_range=stem.motorid_range, verbose=True)
ms.zero_pose = stem.zero_pose
ms.angle_limits = stem.angle_limits


def go_to(ms, pose, margin=10.0, timeout=5.0):
    start = time.time()
    ms.pose = pose

    while (time.time() - start < timeout and
           max(abs(p - tg) for p, tg in zip(ms.pose, pose) if tg is not None) > 10):
        time.sleep(0.1)

ms.moving_speed = [ None,   100,  None, None, None, None]
ms.torque_limit = [ None,    50,  None, None, None, None]
ms.compliant    = [ True, False,  True, True, True, True]
time.sleep(0.1)

go_to(ms, [None, 0.0, None, None, None, None], timeout=10.0)


ms.moving_speed = [ None,   100,   100, None, None, None]
ms.torque_limit = [ None,    50,    50, None, None, None]
ms.compliant    = [ True, False, False, True, True, True]
time.sleep(0.1)

go_to(ms, [None, 0.0, 0.0, None, None, None], timeout=10.0)


print(ms.pose)
