if (simGetScriptExecutionCount() == 0) then
	simAddStatusbarMessage("Getting handles...")
	handles = {}
	handles[1] = simGetObjectHandle("vx64_1")
	handles[2] = simGetObjectHandle("vx64_2")
	handles[3] = simGetObjectHandle("vx64_3")
	handles[4] = simGetObjectHandle("vx28_4")
	handles[5] = simGetObjectHandle("vx28_5")
	handles[6] = simGetObjectHandle("vx28_6")
	cube = simGetObjectHandle("cube")
	simAddStatusbarMessage("Getting handles... done.")

	simAddStatusbarMessage("Getting scripts parameters...")
	
	Trajectory = simUnpackFloats(simGetScriptSimulationParameter(sim_handle_self, "Trajectory"))
	
	motors_sim_steps = math.floor(Trajectory[1])
	max_sim_steps    = math.floor(Trajectory[2])
	max_speed        = Trajectory[3]

	simAddStatusbarMessage("Getting scripts parameters... done.")

	sim_step = simGetScriptExecutionCount()

	-- will be return
	object_sensors = {}
	joint_sensors  = {}

	for i = 1, #handles do
		simSetObjectFloatParameter(handles[i], 2017, max_speed)
	end

end

-- during the simulation
if (simGetScriptExecutionCount() > 0) then
	simHandleChildScript(sim_handle_all_except_explicit) -- make sure children are executed !
	
	pc = simGetObjectPosition(cube, -1)
	for i = 1, 3 do table.insert(object_sensors, pc[i]) end

	qc = simGetObjectQuaternion(cube, -1)
	for i = 1, 4 do table.insert(object_sensors, qc[i]) end
	
	lvc, avc = simGetObjectVelocity(cube)
	for i = 1, 3 do table.insert(object_sensors, lvc[i]) end
	for i = 1, 3 do table.insert(object_sensors, avc[i]) end

	sim_step = simGetScriptExecutionCount()

	function ReadMotorsPosVel(_index)
		joint_sensors[2 * (_index-1) * motors_sim_steps + sim_step] = simGetJointTargetPosition(handles[_index])
		joint_sensors[(2 * (_index-1) + 1) * motors_sim_steps + sim_step] = simGetObjectFloatParameter(handles[_index], 2012)
	end
	for i = 1, #handles do
		ReadMotorsPosVel(i)
	end

	if(sim_step <= motors_sim_steps) then
		for i = 1, #handles do
			simSetJointTargetPosition(handles[i], Trajectory[3 + (i-1) * motors_sim_steps + sim_step])
		end
	end

	if(sim_step > max_sim_steps) then
		simSetScriptSimulationParameter(sim_handle_self, "Object_Sensors", simPackFloats(object_sensors))
		simSetScriptSimulationParameter(sim_handle_self, "Joint_Sensors",  simPackFloats(joint_sensors))
		simPauseSimulation()
	end
end

-- Recommended in documentation : see doc
if (simGetSimulationState()==sim_simulation_advancing_lastbeforestop) then
    -- Put some restoration code here
end
