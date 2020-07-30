"""Aimsun Corridor
"""
from intersection import Intersection
from uuid import uuid4
from config import *



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
    reward : TYPE
        Description
    """
    
    def __init__(self, intersections):
        """Initialize Corridor object
        
        Parameters
        ----------
        intersections : list
            a list of intersection configurations
        """
        self.intx_1 = Intersection(intersections[0])
        self.intx_2 = Intersection(intersections[1])
        self.joint_state = ([], uuid4().int) # ([joint state], flag)
        self.reward = (0, uuid4().int) # (global reward, flag)
        self.action_flag = 0

    def _write_state_reward(self):
        """Send joint state and reward to DQN
        """
        # TODO: write states and cumulative reward to file
        #       STATE and REWARD

        self.reward = (0, uuid4().int) # clear reward

    def _read_action(self):
        """Read and return the actions from DQN
        
        Returns
        -------
        int, int
            action1, action2 from DQN
        """
        flag = self.action_flag
        while flag == self.action_flag
            try:
                # TODO: read ACTION file and update flag
                #       file content format: 'action1 action2 flag'
                action1 = ...
                action2 = ...
                self.action_flag = ... # new flag read from file
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
        # 1. check-in event
        if (self.intx_1._bus_enter_handler(time) or 
        	self.intx_2._bus_enter_handler(time)):
            # update states based on each intersection
            self.joint_state = ([*self.intx_1.get_state(), 
                                 *self.intx_2.get_state()],
                                 uuid4().int)
            # 2. send new state and previous reward to DQN and clear reward
            #    no need to clear state since get_state() function is synchronous 
            #    to Aimsun
            self._write_state_reward()
            # 3. apply action
            action1, action2 = self._read_action()
            self.intx_1.apply_action(action1)
            self.intx_2.apply_action(action2)
        # 4. check-out event
        if (self.intx_1._bus_out_handler(time) or 
            self.intx_2._bus_out_handler(time)):
            # get_reward() function outputs the last checkout bus reward and then
            # clear the stored reward internally
            r_1 = self.intx_1.get_reward()
            r_2 = self.intx_2.get_reward()
            # cumulative reward between time step t and t + 1
            self.reward += r_1 + r_2
        return 0


