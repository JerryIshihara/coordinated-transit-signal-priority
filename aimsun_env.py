import numpy as np
import time
import sys
import csv
import random
from config import *
from env import Environment

Scenario_End = LOG_PATH + 'Scenario_End.txt'
Temp_Reward = LOG_PATH + 'Temp_Reward.txt'
Num_bus_in_rep = LOG_PATH + 'Num_bus_in_rep.txt'


# Initialize reward
wh1 = 0.2
wh2 = 0.45
hdySchd = 4 * 60 + 50  # scheduled headway
term_thres = 0.1


class AimsunEnv(Environment):

    def __init__(self, name, action_space):
        Environment.__init__(self, name=name, action_space=action_space)
        self.state_flag = 0
        self.action_flag = 1
        self.frame_num = 0
        self.num_bus = 0

    def _compute_and_log_reward(self, frmAimsun):
        # compute reward
        travelTime = float(frmAimsun[5])        
        d_in = np.absolute(float(frmAimsun[8]) - float(frmAimsun[7]) - 290)
        d_out = np.absolute(float(frmAimsun[4]) - float(frmAimsun[3]) - 290)
        improve = d_in - d_out
        reward = 0.6 * improve - 0.4 * travelTime
        reward = 1/(1 + np.exp(-reward))
        # Log reward
        with open(self.REWARD_LOG, "a+") as out:  
            csv_write = csv.writer(out, dialect='excel')
            csv_write.writerow([reward])
        return reward

    def _write_action(self, index):
        is_written = False
        while not is_written:
            try:
                f = open(self.ACTION_LOG, "w+")
                f.write("{} {} {}".format(self.action_space[index][0], self.action_space[index][1], self.action_flag))
                f.close()
                is_written = True
                self.action_flag *= -1
            except:
                continue

    def _get_state(self):
        is_read = False
        while not is_read:
            try:
                f = open(self.STATE_LOG, "r")
                frmAimsun = f.read()
                f.close()
                frmAimsun = frmAimsun.split()
            except:
                continue

            if len(frmAimsun) > 0 and int(frmAimsun[-1]) != self.state_flag:
                self.state_flag = int(frmAimsun[-1])
                S_ = np.array([float(frmAimsun[0]), 
                               float(frmAimsun[1]), 
                               float(frmAimsun[2])])
                S_ = S_.reshape(1, len(S_))
                is_read = True

        return S_, frmAimsun

        

    def step(self, action_index):
        self._write_action(action_index)
        S_, frmAimsun = self._get_state()
        reward = self._compute_and_log_reward(frmAimsun)
        if self.num_bus < 50 or self.num_bus % 1000 == 0:
            print("="*20 + " Step: {} ".format(self.num_bus) + "="*20)     
        self.num_bus += 1
        return S_, reward, False, False

    def reset(self):
        # is_written = False
        # while not is_written:
        #     try:
        #         f = open(TransferToDQN, "w+")
        #         f.write("")
        #         f.close()
        #         f = open(ACTION, "w+")
        #         f.write("")
        #         f.close()
        #         is_written = True
        #     except Exception as e:
        #         print("reset ERROR: " + e)
        #         continue

        S_, frmAimsun = self._get_state()
        return S_


    def get_num_bus_in_rep(self):
        num_bus = []
        while len(num_bus) != 1:
            try:
                f = open(Num_bus_in_rep, "r")
                num_bus = f.read()
                f.close()
                num_bus = num_bus.split()
            except:
                continue

            if len(num_bus) != 0:
                print(num_bus[0])
                return int(num_bus[0])

    





