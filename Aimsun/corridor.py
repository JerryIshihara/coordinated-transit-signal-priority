"""Aimsun Corridor
"""
from uuid import uuid4
import os, sys, inspect
# import numpy as np
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from config import *
from intersection import *
from prePOZ import *


class Corridor:

    """Summary
    
    Attributes
    ----------
    action_flag : int
        Description
    intx_1 : TYPE
        Description
    intx_2 : TYPE
        Description
    joint_state : TYPE
        Description
    """
    
    def __init__(self, intersections):
        """Initialize Corridor object
        
        Parameters
        ----------
        intersections : list
            a list of intersection configurations
        """
        # first prePOZ + POZ
        self.intx_1 = Intersection(intersections[0])
        self.prePOZ_1 = PrePOZ(intersections[0]['prePOZ'])
        
        # second prePOZ + POZ
        self.intx_2 = Intersection(intersections[1])
        self.prePOZ_2 = PrePOZ(intersections[1]['prePOZ'])

        self.joint_state = ([], uuid4().int) # ([joint state], flag)
        self.action_flag = 0

    def _write_state_reward(self, reward):
        """Send joint state and reward to DQN
        """
        is_reward_written = False
        while not is_reward_written:
            try:
                f = open(REWARD, "w+")
                f.write("{} {}".format(reward, uuid4().int))
                f.close()
                is_reward_written = True
            except:
                print("")
                continue
        
        joint_state = self.joint_state
        joint_state_str = ' '.join(str(n) for n in joint_state[0])
        is_state_written = False
        while not is_state_written:
            try:
                f = open(STATE, "w+")
                f.write("{} {}".format(joint_state_str, joint_state[1]))
                f.close()
                is_state_written = True
            except:
                continue
        
    def _read_action(self):
        """Read and return the actions from DQN
        
        Returns
        -------
        int, int
            action1, action2 from DQN
        """
        flag = self.action_flag
        while flag == self.action_flag:
            try:
                f = open(ACTION, "r")
                data = f.read()
                f.close()
                data = data.split()
                if len(data) != 3: 
                    continue
                action1 = int(data[0])
                action2 = int(data[1])
                self.action_flag = int(data[2]) # new flag read from file
            except:
                continue
        return action1, action2

    def aapi_post_manage(self, time, timeSta, timeTrans, acycle):
        """A life cycle in Aimsun where replication is currently running
        
        Parameters
        ----------
        time : int
            current replication time in Aimsun
        timeSta : int
            defaul Aimsun input
        timeTrans : int
            defaul Aimsun input
        acycle : int
            defaul Aimsun input
        
        Returns
        -------
        int
            0 indicates successful function call to Aimsun Next
        """
        # prePOZ update
        self.prePOZ_1.update(time, timeSta)
        self.prePOZ_2.update(time, timeSta)
        # check-out event
        self.intx_1._bus_out_handler(time, timeSta)
        self.intx_2._bus_out_handler(time, timeSta)
        # check-in event
        intx1_bus_checkin = self.intx_1._bus_enter_handler(time, timeSta)
        intx2_bus_checkin = self.intx_2._bus_enter_handler(time, timeSta)
        if ( intx1_bus_checkin or intx2_bus_checkin ):
            # update states based on each intersection
            pre1 = self.prePOZ_1.get_state()
            pre2 = self.prePOZ_2.get_state()
            poz1 = self.intx_1.get_state()
            poz2 = self.intx_2.get_state()
            self.joint_state = (pre1 + poz1 + pre2 + poz2, uuid4().int)
            #    - send new state and previous reward to DQN and clear reward
            #      no need to clear state since get_state() function is synchronous 
            #      to Aimsun
            #    - use get_reward() function to fetch cumulative reward in each intersection 
            #      since last timestep clear the stored reward internally
            r_1 = self.intx_1.get_reward()
            r_2 = self.intx_2.get_reward()
            # cumulative reward between time step t and t + 1
            total_reward = r_1 + r_2
            # total_reward = 1 / (1 + np.exp(-total_reward))
            self._write_state_reward(total_reward)
            # apply action
            action1, action2 = self._read_action()
            # record the action decided to the checked in bus
            if intx1_bus_checkin:
                self.intx_1.set_bus_actions_and_state([action1, action2], pre1 + poz1 + pre2 + poz2)
            if intx2_bus_checkin:
                self.intx_2.set_bus_actions_and_state([action1, action2], pre1 + poz1 + pre2 + poz2)
            # apply action to each intersection
            if self.intx_1.numbus == 0:
                action1 = 0  # if there is no bus in intx 1, no action can be applied
            self.intx_1.apply_action(action1, time, timeSta)
            self.intx_2.apply_action(action2, time, timeSta)

        
        return 0


