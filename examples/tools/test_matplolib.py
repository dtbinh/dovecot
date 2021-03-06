"""
	Read a logegr file to print or show value :

	Datas are like this :
		[timestamp, datas[order_time, object_sensors, vrep_time, opti_traj, tip_sensors, joint_sensors, order, effect, vrep_traj]]
"""

import sys
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from itertools import product, combinations
from matplotlib.patches import Rectangle, Circle, PathPatch
import mpl_toolkits.mplot3d.art3d as art3d

from dovecot.logger import logger
from dovecot import ttts

CALIBDIR = '~/.dovecot/tttcal/'

def not_implemented(datas):
	print "Plot for these data is not implemented yet."

def load_file(folder, filename):
	l = logger.Logger(folder=folder, filename=filename)
	return l.load()

def show_opti_traj(datas):
	fig = plt.figure()
	ax = fig.gca(projection='3d')
	for data in datas:
		xs, ys, zs = [], [], []
		t_stamp = data['timestamp']
		opti_traj = data['datas']['opti_traj']
		for traj in opti_traj:
			 xs.append(traj[1][0])
			 ys.append(traj[1][1])
			 zs.append(traj[1][2])
		ax.plot(xs, ys, zs) #, label='parametric curve' + str(t_stamp))
	ax.legend("opti_traj")
	plt.show()

def show_vrep_traj(datas):
	fig = plt.figure()
	ax = fig.gca(projection='3d')
	ax.set_aspect("equal")

	if len(datas) > 0:
		scene = datas[0]['datas']['scene']
		calibdata = load_calib_scene(scene)
		if scene.startswith("vrep_"):
			scene = scene[5:]
		if scene.startswith("ar_"):
			scene = scene[3:]
		draw_toy(ax, scene, calibdata)

	for data in datas:
		xs, ys, zs = [], [], []
		t_stamp = data['timestamp']
		vrep_traj = data['datas']['vrep_traj']
		effect = data['datas']['effect']
		for traj in vrep_traj:
			 xs.append(traj[1][0])
			 ys.append(traj[1][1])
			 zs.append(traj[1][2])
		if effect[2] > 0:
			ax.plot(xs, ys, zs, c=(1,0,1,0.3))
		#else:
			#ax.plot(xs, ys, zs, c=(0,0,1,0.1))
	ax.legend()
	plt.show()

def load_calib_scene(scene):
	caldata = ttts.TTTCalibrationData(scene, CALIBDIR)
	caldata.load()
	return caldata

def draw_toy(ax, toy, calibdata):
	pos = calibdata.position_world

	print(pos)

	dim = calibdata.dimensions

	if toy == "center_cube":
		# eurk code
		xe = [pos[0] - dim[0] / 200, pos[0] + dim[0] / 200]
		ye = [pos[1] - dim[1] / 200, pos[1] + dim[1] / 200]
		ze = [pos[2] - dim[2] / 200, pos[2] + dim[2] / 200]
		for s, e in combinations(np.array(list(product(xe,ye,ze))), 2):
			if np.sum(np.abs(s-e)) == xe[1]-xe[0] or np.sum(np.abs(s-e)) == ye[1]-ye[0] or np.sum(np.abs(s-e)) == ze[1]-ze[0]:
				ax.plot(*zip(s,e), color=(0,0,1,0.5))
		pass
	elif toy == "cylinder":
		pass
	elif toy == "sphere":
		pass
	else:
		pass


def show_collide_data(datas):
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	#ax.set_aspect("equal")
	# toy
	if len(datas) > 0:
		scene = datas[0]['datas']['scene']
		calibdata = load_calib_scene(scene)
		if scene.startswith("vrep_"):
			scene = scene[5:]
		if scene.startswith("ar_"):
			scene = scene[3:]
		draw_toy(ax, scene, calibdata)

	# collide data
	for data in datas:
		col = data['datas']['collide_data']
		if len(col) == 3:
			ax.scatter(col[0], col[1], col[2], c='r', marker='o')
	ax.legend()
	plt.show()

def show_order_time(datas):
	fig = plt.figure()
	ax = fig.add_subplot(111)
	ts_tab = []
	ot_tab = []
	for data in datas:
		ts_tab.append(data['timestamp'])
		ot_tab.append(data['datas']['order_time'])

	ax.plot(ts_tab, ot_tab)
	plt.ylabel('order_time')
	plt.show()

def list_all_keyword(datas):
	print "All valid keywords :"
	for key in dispatch.keys():
		if dispatch[key] != not_implemented:
			print "  {}".format(key)

dispatch = {
    'order_time': show_order_time,
    'object_sensors': not_implemented,
    'vrep_time': not_implemented,
    'opti_traj': show_opti_traj,
    'tip_sensors': not_implemented,
    'joint_sensors': not_implemented,
    'order': not_implemented,
    'effect': not_implemented,
    'vrep_traj': show_vrep_traj,
    'collide_data' : show_collide_data,
    'scene' : not_implemented
}

def main():
	if len(sys.argv) != 4:
		print "usage : python {} <log path> <log name> --list".format(sys.argv[0])
	else:
		folder = sys.argv[1]
		fname = sys.argv[2]
		option = sys.argv[3]
		datas = load_file(folder, fname)
		if option == "--list":
			list_all_keyword(datas)
		elif option.startswith("--"):
			print "error : {} is not a valid option".format(option)
			print "usage : python {} <log path> <log name> --list".format(sys.argv[0])
		else:
			print "Showing plot for \"{}\"".format(sys.argv[3])
			try:
				dispatch[option](datas)
			except KeyError:
				print "{} is not a valid keyword.".format(option)

if __name__ == '__main__':
	main()
