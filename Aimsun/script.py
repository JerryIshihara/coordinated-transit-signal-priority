from AAPI import *
import os, sys, inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from config import *
from corridor import *


def AAPILoad():
    """
    Create Intersection objects. Called when the module is loaded by Aimsum Next
    """
    global corridor
    corridor = Corridor(CORRIDOR)
    return 0


def AAPIInit():
    """Summary
    Initializes the module. Called when Aimsum Next starts the simulation
    """
    ANGConnEnableVehiclesInBatch(True)
    return 0


def AAPIManage(time, timeSta, timeTrans, acycle):
    """Summary
       Called in every simulation step at the beginning of the cycle, and can be used to update states 
       and output states to DQN, and implement TSP stategies
    
    Parameters
    ----------
    time : double
        Absolute time of simulation in seconds
    timeSta : double
        Time of simulation in stationary period, in seconds
    timeTrans : double
        Duration of warm-up period, in seconds
    acycle : double
        Duration of each simulation step in seconds
    """
    return 0


def AAPIPostManage(time, timeSta, timeTrans, acycle):
    """Summary
    Called in every simulation step at the beginning of the cycle, and can be used to update states 
    and output states to DQN, and implement TSP stategies
       
    Parameters
    ----------
    time : double
        Absolute time of simulation in seconds
    timeSta : double
        Time of simulation in stationary period, in seconds
    timeTrans : double
        Duration of warm-up period, in seconds
    acycle : double
        Duration of each simulation step in seconds
    """
    global corridor
    corridor.aapi_post_manage(time, timeSta, timeTrans, acycle)
    return 0


def AAPIFinish():
    """Summary
    Called when Aimsun Next finishes the simulation and can be used to terminate the module operations, 
    write summary information, close files, etc.
    """
    global corridor
    # write last reward to indicate that the replication is done
    corridor.write_last_reward()
    return 0


def AAPIUnLoad():
    """Summary
    Called when the module is unloaded by Aimsun Next.
    """
    return 0
    