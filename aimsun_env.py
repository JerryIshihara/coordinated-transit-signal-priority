"""AimsunEnv
"""
import sys
import csv
import numpy as np
from uuid import uuid4
from config import *
from env import Environment



class AimsunEnv(Environment):
    """Aimsun Next environment
    
    Attributes
    ----------
    num_step : int
        total time steps simulated
    reward_flag : int
        check if received reward is at the new time step
    state_flag : int
        check if received state is at the new time step

    STATE_INPUT_LEN : int
        state size + 1 (flag)
    REWARD_INPUT_LEN : int
        reward size + 1 (flag)
    """

    REWARD_INPUT_LEN = 2
    STATE_INPUT_LEN = 17
    
    def __init__(self, action_space):
        """Initialize Aimsun Next environment object
        
        Parameters
        ----------
        action_space : list
            list of available actions
        """
        Environment.__init__(self, name='Aimsun', action_space=action_space)
        self.reward_flag = 0
        self.state_flag = 0
        self.num_step = 0

    def _receive_and_log_reward(self):
        """Receive, log and return the new reward
        
        Returns
        -------
        float
            newly received reward
        """
        # receive from REWARD_LOG
        is_read = False
        while not is_read:
            try:
                f = open(self.REWARD_LOG, "r")
                data = f.read()
                f.close()
                data = data.split()
                if len(data) != REWARD_INPUT_LEN: continue
                reward, new_flag = float(data[0]), int(data[1])
                if new_flag != self.reward_flag:
                    is_read = True
                    self.reward_flag = new_flag
            except:
                continue
        # write to REWARD_CSV for later analysis
        with open(self.REWARD_CSV, "a+") as out:  
            csv_write = csv.writer(out, dialect='excel')
            csv_write.writerow([reward])
        return reward

    def _write_action(self, index):
        """write the newly received action to Aimsun
        
        Parameters
        ----------
        index : int
            the index of the new action
        """
        is_written = False
        while not is_written:
            try:
                f = open(self.ACTION_LOG, "w+")
                f.write("{} {} {}".format(self.action_space[index][0], self.action_space[index][1], uuid4().int))
                f.close()
                is_written = True
            except:
                continue

    def _get_state(self):
        """Receive and return the new state
        
        Returns
        -------
        list
            received state
        """
        is_read = False
        while not is_read:
            try:
                f = open(self.STATE_LOG, "r")
                data = f.read()
                f.close()
                data = data.split()
                if len(data) != STATE_INPUT_LEN: continue
                new_flag = int(data[-1])
                if new_flag != self.state_flag:
                    S_ = np.array(map(lambda x: float(x), data[:-1]))
                    is_read = True
                    self.state_flag = new_flag
            except:
                continue
        self.num_step += 1
        return S_

    def step(self, action_index):
        """Apply the write the action to Aimsun and wait for the new
        state and reward
        
        Parameters
        ----------
        action_index : int
            the index of the action space
        
        Returns
        -------
        list, float, bool
            new state, new reward, and simulation finish
        """
        self._write_action(action_index)
        S_ = self._get_state()
        reward = self._receive_and_log_reward()
        # print log
        if self.num_step < 50 or self.num_step % 1000 == 0:
            print("="*20 + " Step: {} ".format(self.num_step) + "="*20)
        return S_, reward, False

    def reset(self):
        """Reset the Aimsun environment and receive the first state
        """
        print('Reset Aimsun Environment')
        print('Waiting for the first bus...')
        return self._get_state()

    # TODO: indicate the first bus in each rep
    # def get_num_bus_in_rep(self):
    #     """Summary
        
    #     Returns:
    #         TYPE: Description
    #     """
    #     num_bus = []
    #     while len(num_bus) != 1:
    #         try:
    #             f = open(Num_bus_in_rep, "r")
    #             num_bus = f.read()
    #             f.close()
    #             num_bus = num_bus.split()
    #         except:
    #             continue

    #         if len(num_bus) != 0:
    #             print(num_bus[0])
    #             return int(num_bus[0])

    





