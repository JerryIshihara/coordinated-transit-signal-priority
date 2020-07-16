import numpy as np
import time
import sys
import csv
import random
from config import *


TransferToDQN = LOG_PATH + 'TransferToDQN.txt'
ACTION = LOG_PATH + 'ACTION.txt'
Scenario_End = LOG_PATH + 'Scenario_End.txt'
Reward_log = LOG_PATH + 'Reward.csv'
Temp_Reward = LOG_PATH + 'Temp_Reward.txt'
Num_bus_in_rep = LOG_PATH + 'Num_bus_in_rep.txt'


# Initialize reward
wh1 = 0.2
wh2 = 0.45
hdySchd = 4 * 60 + 50  # scheduled headway
term_thres = 0.1


class AimsunEnv(Environment):

    def __init__(self, debug=False, name, action_space):
        Environment.__init__(self, name=name, action_space=action_space)
        self.state_flag = 0
        self.action_flag = 1
        self.frame_num = 0
        self.num_bus = 0

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
        frmAimsun = [0]
        start = time.time()
        while not is_read:
            try:
                f = open(self.STATE_LOG, "r")
                frmAimsun = f.read()
                f.close()
                frmAimsun = frmAimsun.split()
            except:
                continue

            senario_end = self.senario_is_end()
            if senario_end:
                if time.time() - start < 60:
                    sys.stdout.write("Training end in {} min  \r".format(2))
                    sys.stdout.flush()
                elif time.time() - start < 90:
                    sys.stdout.write("Training end in {} min  \r".format(1))
                    sys.stdout.flush()
                elif time.time() - start < 120:
                    sys.stdout.write("Training end in {:.2f} sec  \r".format(120 - (time.time() - start)))
                    sys.stdout.flush()
                elif time.time() - start > 300:
                    sys.stdout.write("Reset  \r")
                    sys.stdout.flush()
                    return [], 0, False, True

            if len(frmAimsun) != 0 and float(frmAimsun[-1]) != self.state_flag:
                self.state_flag = float(frmAimsun[-1])
                # states = (target travel time, time to the end of the next green phase, No. of veh)
                S_ = np.array(
                    [float(frmAimsun[0]), float(frmAimsun[1]), float(frmAimsun[2])])  # variables defining states
                S_ = np.reshape(S_, (1, 3))
            else:
                frmAimsun = [0]

    def step(self, action_index):

        self._write_action(action_index)
        S_ = self._get_state()

        # frmAimSun = [0]
        # start = time.time()
        # while len(frmAimSun) < 2:
        #     try:
        #         f = open(TransferToDQN, "r")
        #         frmAimSun = f.read()
        #         f.close()
        #         frmAimSun = frmAimSun.split()
        #     except:
        #         continue

        #     senario_end = self.senario_is_end()
        #     if senario_end:
        #         if time.time() - start < 60:
        #             sys.stdout.write("Training end in {} min  \r".format(2))
        #             sys.stdout.flush()
        #         elif time.time() - start < 90:
        #             sys.stdout.write("Training end in {} min  \r".format(1))
        #             sys.stdout.flush()
        #         elif time.time() - start < 120:
        #             sys.stdout.write("Training end in {:.2f} sec  \r".format(120 - (time.time() - start)))
        #             sys.stdout.flush()
        #         elif time.time() - start > 300:
        #             sys.stdout.write("Reset  \r")
        #             sys.stdout.flush()
        #             return [], 0, False, True

        #     if len(frmAimSun) != 0 and float(frmAimSun[-1]) != self.state_flag:
        #         self.state_flag = float(frmAimSun[-1])
        #         # states = (target travel time, time to the end of the next green phase, No. of veh)
        #         S_ = np.array(
        #             [float(frmAimSun[0]), float(frmAimSun[1]), float(frmAimSun[2])])  # variables defining states
        #         S_ = np.reshape(S_, (1, 3))
        #     else:
        #         frmAimSun = [0]

        outLead = float(frmAimSun[3])
        outFollow = float(frmAimSun[4])
        travelTime = float(frmAimSun[5])
        # remain = float(frmAimSun[7])
        remain = float(frmAimSun[6])
        # updated = float(frmAimSun[-1])

        # hdyDiff = outLead - outFollow
        hdyDiff = outFollow - outLead

        
        if travelTime == 0:
            print("ManType Error : Zero Division -- travelTime==0")
            travelTime = 100
            
        
        ############################## travel time reward#############################
        # penalty = float(frmAimSun[9])
        # reward = -1 * (travelTime + penalty)

        ############################## improvememt reward #############################
        d_in = np.absolute(float(frmAimSun[8]) - float(frmAimSun[7]) - 290)
        d_out = np.absolute(float(frmAimSun[4]) - float(frmAimSun[3]) - 290)
        improve = d_in - d_out
        reward = 0.6 * improve - 0.4 * travelTime
        reward = 1/(1 + np.exp(-reward))




        ########################### log ###########################
        try:
            log = [reward]
            with open(Reward_log, "a+") as out:  # Log reward
                csv_write = csv.writer(out, dialect='excel')
                csv_write.writerow(log)
        except Exception as e:
            print(e)


        is_written = False
        while not is_written:
            try:
                f = open(Temp_Reward, "w+")
                for i in output:
                    f.write("{} ".format(reward))
                f.close()
                is_written = True
            except:
                print("failed writing files")
                continue
        ######################################################
        if self.num_bus < 50 or self.num_bus % 100 == 0:
            print("==================== Step: {} ====================".format(self.num_bus)) #delete
            print("Env.step()---inTime[-1]={} outTime[-1]={} inTime[-2]={} outTime[-2]={}: ".format(frmAimSun[8], frmAimSun[4], frmAimSun[7], frmAimSun[3]))        
            print("Env.step()---hdyDiff={} hdySchd={} travelTime={} remain={}: ".format(hdyDiff, hdySchd, travelTime, remain))
            print("Env.step()---reward: {}".format(reward))
            print("Env.step()---state: " + str(S_))
        self.num_bus += 1
        return S_, reward, False, False

    def reset(self):
        print("=== RESET ===")
        print("Action Space: {}".format(self.action_space))
        is_written = False
        while not is_written:
            try:
                f = open(TransferToDQN, "w+")
                f.write("")
                f.close()
                f = open(ACTION, "w+")
                f.write("")
                f.close()
                is_written = True
            except Exception as e:
                print("reset ERROR: " + e)
                continue

        is_written = False
        while not is_written:
            try:
                f = open(Scenario_End, "w+")
                f.write("{} ".format(0))
                f.close()
                is_written = True
            except Exception as e:
                print("reset error: " + e)
                continue


        frmAimSun = [0]
        while len(frmAimSun) < 2:
            try:
                f = open(TransferToDQN, "r")
                frmAimSun = f.read()
                f.close()
                frmAimSun = frmAimSun.split()
            except:
                print("ERROR: cannot read TransferToDQN.txt")
                f = open(TransferToDQN, "w+")
                f.write("")
                f.close()
                continue

            if len(frmAimSun) != 0 and float(frmAimSun[-1]) != self.state_flag:
                self.state_flag = float(frmAimSun[-1])
                # states = (target travel time, time to the end of the next green phase, No. of veh)
                S_ = np.array(
                    [float(frmAimSun[0]), float(frmAimSun[1]), float(frmAimSun[2])])  # variables defining states
                S_ = np.reshape(S_, (1, 3))
            else:
                frmAimSun = [0]

        print(S_)
        return S_


    def rand_action(self):
        return np.random.randint(0, len(self.action_space))

    def senario_is_end(self):
        senario = []
        while len(senario) != 1:
            try:
                f = open(Scenario_End, "r")
                senario = f.read()
                f.close()
                senario = senario.split()
            except:
                continue

            if len(senario) != 0:
                return True if float(senario[0]) == 1 else False



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

    





