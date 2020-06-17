"""
Giacomo Spigler
"""
import numpy as np
import time
import sys
import csv
# from scipy.misc import imresize
import random

CWD = 'C:/Users/Public/Documents/ShalabyGroup/aimsun_ddqn_server/log_files/'
TransferToDQN = CWD + 'TransferToDQN.txt'
TransferToAimsun = CWD + 'TransferToAimsun.txt'
Scenario_End = CWD + 'Scenario_End.txt'
Reward_log = CWD + 'Reward.csv'
Temp_Reward = CWD + 'Temp_Reward.txt'
Num_bus_in_rep = CWD + 'Num_bus_in_rep.txt'


# Initialize reward
wh1 = 0.2
wh2 = 0.45
hdySchd = 4 * 60 + 50  # scheduled headway
term_thres = 0.1


class AimsunEnv:
    """
    Wrapper for OpenAI Gym Atari environments that returns the last 4 processed frames.
    Input frames are converted to grayscale and downsampled from 120x160 to 84x112 and cropped to 84x84 around the game's main area.
    The final size of the states is 84x84x4.

    If debug=True, an OpenCV window is opened and the last processed frame is displayed. This is particularly useful when adapting the wrapper to novel environments.
    """

    def __init__(self, debug=False):
        self.state_flag = 0
        self.env_name = "aimsun"
        self.debug = debug
        self.action_space = [(1,-20), (1,-15), (1,-10), (1,-5), (1,0), (1,5), (1,10), (1,15), (1,20)] # available actions

        self.frame_num = 0
        self.action_flag = 1
        self.num_bus = 0

    # def seed(self, seed=None):
    #     return self.env._seed(seed)

    def step(self, a):
        output = [self.action_space[a], self.action_flag]
        print("Env.step()---action: " + str(output))
        self.action_flag *= -1

        is_written = False
        while not is_written:
            try:
                f = open(TransferToAimsun, "w+")
                f.write("{} {} {}".format(output[0][0], output[0][1], output[1]))
                f.close()
                is_written = True
            except:
                print("failed writing files")
                continue

        frmAimSun = [0]
        start = time.time()
        while len(frmAimSun) < 2:
            try:
                f = open(TransferToDQN, "r")
                frmAimSun = f.read()
                f.close()
                frmAimSun = frmAimSun.split()
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

            if len(frmAimSun) != 0 and float(frmAimSun[-1]) != self.state_flag:
                self.state_flag = float(frmAimSun[-1])
                # states = (target travel time, time to the end of the next green phase, No. of veh)
                S_ = np.array(
                    [float(frmAimSun[0]), float(frmAimSun[1]), float(frmAimSun[2]), float(frmAimSun[5]) - 290])  # variables defining states
                S_ = np.reshape(S_, (1, 4))
            else:
                frmAimSun = [0]

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
        reward = (0.6 * improve - 0.4 * travelTime)




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
                f = open(TransferToAimsun, "w+")
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
                    [float(frmAimSun[0]), float(frmAimSun[1]), float(frmAimSun[2]), float(frmAimSun[5]) - 290])  # variables defining states
                S_ = np.reshape(S_, (1, 4))
            else:
                frmAimSun = [0]

        print(S_)
        return S_


    def rand_action(self):
        return np.random.randint(0, 4)

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

    





