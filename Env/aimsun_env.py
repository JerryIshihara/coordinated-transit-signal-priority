"""AimsunEnv
"""
import os, sys, inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from config import *
import csv
import numpy as np
from uuid import uuid4
from .env import Environment


REWARD_INPUT_LEN = 2
STATE_INPUT_LEN = 17

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
    """
    
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
        self.check_in_time = []

    def get_state_size(self):
        """Return the state size
        
        Returns
        -------
        int
            state size
        """
        return STATE_INPUT_LEN - 1

    def get_action_size(self):
        """Return the action space size
        
        Returns
        -------
        int
            action space size
        """
        return len(self.action_space)

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
                    S_ = np.array(list(map(lambda x: float(x), data[:-1])))
                    self.check_in_time.append(max(S_[3], S_[11]))
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

    def exclude(self):
        """Summary
        
        Returns:
            TYPE: Description
        """
        if len(self.check_in_time) > 10: self.check_in_time.pop(0)
        if len(self.check_in_time) <= 2: return True
        if self.check_in_time[-1] < self.check_in_time[-2]:
            return True
        return False

    





