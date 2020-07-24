import os, sys, inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from config import *
from intersection import *
from corridor import *


def AAPILoad():
    """Summary

    Returns
    -------
    TYPE
        Description
    """
    global intersections
    intersections = Corridor(CORRIDOR)
    return 0


def AAPIInit():
    """Summary

    Returns
    -------
    TYPE
        Description
    """
    ANGConnEnableVehiclesInBatch(True)
    return 0


def AAPIManage(time, timeSta, timeTrans, acycle):
    """Summary

    Parameters
    ----------
    time : TYPE
        Description
    timeSta : TYPE
        Description
    timeTrans : TYPE
        Description
    acycle : TYPE
        Description

    Returns
    -------
    TYPE
        Description
    """
    return 0


def AAPIPostManage(time, timeSta, timeTrans, acycle):
    """Summary

    Parameters
    ----------
    time : TYPE
        Description
    timeSta : TYPE
        Description
    timeTrans : TYPE
        Description
    acycle : TYPE
        Description

    Returns
    -------
    TYPE
        Description
    """
    global intersections
    corridor.aapi_post_manage(time, timeSta, timeTrans, acycle)
    return 0


def AAPIFinish():
    """Summary

    Returns
    -------
    TYPE
        Description
    """
    return 0


def AAPIUnLoad():
    """Summary

    Returns
    -------
    TYPE
        Description
    """
    return 0
