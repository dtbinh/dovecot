import treedict

cfg = treedict.TreeDict()
cfg.vrep.ppf = 10

cfg.sprims.names = ['push']
cfg.sprims.uniformze = False

cfg.mprim.name = 'dmpg'
cfg.mprim.motor_steps = 2000 
cfg.mprim.max_steps   = 2000
cfg.mprim.uniformze   = False
cfg.mprim.n_basis     = 2
cfg.mprim.max_speed   = 1.0
cfg.mprim.end_time    = 1.25

cfg.mprim.init_states   = [-30.0, 0.0, 0.0, 0.0, 0.0, 0.0]
cfg.mprim.target_states = [ 30.0, 0.0, 0.0, 0.0, 0.0, 0.0]