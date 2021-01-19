#######################################################################################
# Deep Q - Learning framework to play around with (dueling-, dense- and double q-learning )
# Author: Manuel Hass
# 2017
# 
# *uses mlp_framework.py as model framework 
# *examples in the end
#######################################################################################


### imports
import numpy as np
from numpy import linalg as LA
import time
import csv
import pickle
import os, sys, inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from config import *

Q_target_log =  LOG_PATH + 'Q_target.csv'
Q_online_log = LOG_PATH + 'Q_online.csv'
Rt_log = LOG_PATH + 'Rt.csv'
Loss = LOG_PATH + 'loss.csv'



def write_csv(path, data):
    with open(path, "a+") as out:  
        csv_write = csv.writer(out, dialect='excel')
        csv_write.writerow(data)

# helper functions
def train_bellman(onlineDQN, targetDQN, batch, GAMMA):
    '''
    updates the onlineDQN with target Q values for the greedy action(chosen by onlineDQN)
    '''

    state, action, reward, next_state, done = batch
    Q = onlineDQN.infer(state)
    t = targetDQN.infer(next_state)
    a = np.argmax(onlineDQN.infer(next_state), axis=1)
    Q[range(Q.shape[0]), action.astype(int)] = reward + np.logical_not(done) * GAMMA * t[range(t.shape[0]), a]
    state_batch_ = state
    target_batch_ = Q

    onlineDQN.train(state_batch_, target_batch_)


def update_target(onlineDQN, targetDQN, duel=False):
    '''
    copies weights from onlineDQN to targetDQN
    '''
    if duel:
        for i in range(len(targetDQN.LL0)):
            targetDQN.LL0[i].w = np.copy(onlineDQN.LL0[i].w)
        for i in range(len(targetDQN.LLA)):
            targetDQN.LLA[i].w = np.copy(onlineDQN.LLA[i].w)
        for i in range(len(targetDQN.LLV)):
            targetDQN.LLV[i].w = np.copy(onlineDQN.LLV[i].w)
    else:
        for i in range(len(targetDQN.Layerlist)):
            targetDQN.Layerlist[i].w = np.copy(onlineDQN.Layerlist[i].w)
    
        beta = 0.9
        for i in range(len(targetDQN.Layerlist)):
            targetDQN.Layerlist[i].w = beta * np.copy(onlineDQN.Layerlist[i].w) + (1 - beta) * targetDQN.Layerlist[i].w


class ringbuffer:
    '''
    fast ringbuffer for the experience replay (numpy)
    '''

    def __init__(self, SIZE):
        self.buffer_size = 0
        self.SIZE = SIZE
        # buffers
        self.state_buffer = None
        self.action_buffer = None
        self.reward_buffer = None
        self.next_state_buffer = None
        self.done_buffer = None
        self.priorities = None

    def add(self, sample):
        if self.state_buffer is None:
            self.state_buffer = np.empty((0, sample[0].shape[1]))  # [1:]
            self.action_buffer = np.empty((0, sample[1].shape[1]))  # [1:]
            self.reward_buffer = np.empty((0, sample[2].shape[1]))  # [1:]
            self.next_state_buffer = np.empty((0, sample[3].shape[1]))  # [1:]
            self.done_buffer = np.empty((0, 1))  # [1:]
            self.priorities = np.empty((0, 1))  # [1:]
        # self.state_buffer = np.append(self.state_buffer, sample[0][True, :], axis=0)
        self.state_buffer = np.append(self.state_buffer, sample[0], axis=0)
        self.action_buffer = np.append(self.action_buffer, sample[1], axis=0)
        self.reward_buffer = np.append(self.reward_buffer, sample[2], axis=0)
        self.next_state_buffer = np.append(self.next_state_buffer, sample[3], axis=0)
        self.done_buffer = np.append(self.done_buffer, sample[4], axis=0)
        new_sample_prio = np.max(self.priorities) if self.priorities.shape[0] > 0 and np.max(
            np.abs(self.priorities)) < 1e10 else 1.
        self.priorities = np.append(self.priorities, np.array([new_sample_prio]).reshape(1, 1), axis=0)
        self.priorities /= np.sum(self.priorities)
        self.buffer_size += 1.
        if self.buffer_size > self.SIZE:
            self.state_buffer = self.state_buffer[1:]
            self.action_buffer = self.action_buffer[1:]
            self.reward_buffer = self.reward_buffer[1:]
            self.next_state_buffer = self.next_state_buffer[1:]
            self.done_buffer = self.done_buffer[1:]
            self.priorities = self.priorities[1:]

    def delete(self):
        if self.buffer_size > 0:
            # self.state_buffer = np.append(self.state_buffer, sample[0][True, :], axis=0)
            self.state_buffer = np.delete(self.state_buffer, -1, axis=0)
            self.action_buffer = np.delete(self.action_buffer, -1, axis=0)
            self.reward_buffer = np.delete(self.reward_buffer, -1, axis=0)
            self.next_state_buffer = np.delete(self.next_state_buffer, -1, axis=0)
            self.done_buffer = np.delete(self.done_buffer, -1, axis=0)
            self.priorities = np.delete(self.priorities, -1, axis=0)
            self.priorities /= np.sum(self.priorities)
            self.buffer_size -= 1.

    def get(self):
        return [self.state_buffer,
                self.action_buffer,
                self.reward_buffer,
                self.next_state_buffer,
                self.done_buffer]

    def sample(self, BATCHSIZE, prio=False):
        if prio:
            a = self.done_buffer.shape[0]
            c = self.priorities.reshape((a))
            b = c / np.sum(c)
            ind = np.random.choice(np.arange(a), BATCHSIZE, replace=False, p=b).astype(int)
        else:
            ind = np.random.choice(np.arange(self.done_buffer.shape[0]), BATCHSIZE, replace=False).astype(int)

        return [self.state_buffer[ind],
                self.action_buffer[ind].reshape(-1),
                self.reward_buffer[ind].reshape(-1),
                self.next_state_buffer[ind],
                self.done_buffer[ind].reshape(-1)]

    def prio_update(self, onlineDQN, targetDQN, epsilon=0.01, alpha=0.6, GAMMA=0.99, CHUNK=5000.):

        # state,action,reward,next_state,done = self.get()
        getbuffer = self.get()
        # CHUNK = 5000. # max number of states used for inference at once
        loops = int(getbuffer[0].shape[0] / CHUNK)  # number of loops needed to update all prios
        priobuffer = np.empty((0))
        j = -1

        for j in range(loops):  # if replaybuffer size bigger than CHUNK size
            state, action, reward, next_state, done = [x[int(j * CHUNK):int((j + 1) * CHUNK)] for x in getbuffer]
            Q = onlineDQN.infer(state)
            Q_ = np.copy(Q)
            t = targetDQN.infer(next_state)
            a = np.argmax(onlineDQN.infer(next_state), axis=1)
            Q[range(Q.shape[0]), action.astype(int)] = reward + np.logical_not(done) * GAMMA * t[range(t.shape[0]), a]
            TD_loss = np.abs((Q_ - Q))
            TD_loss = TD_loss[range(TD_loss.shape[0]), a]
            prio = np.power((TD_loss + epsilon), alpha)
            prio /= np.sum(prio)
            priobuffer = np.append(priobuffer, prio)

        state, action, reward, next_state, done = [x[int((j + 1) * CHUNK):] for x in getbuffer]
        Q = onlineDQN.infer(state)
        Q_ = np.copy(Q)
        t = targetDQN.infer(next_state)
        a = np.argmax(onlineDQN.infer(next_state), axis=1)
        Q[range(Q.shape[0]), action.astype(int)] = reward + np.logical_not(done) * GAMMA * t[range(t.shape[0]), a]
        TD_loss = np.abs((Q_ - Q))
        TD_loss = TD_loss[range(TD_loss.shape[0]), a]
        prio = np.power((TD_loss + epsilon), alpha)
        prio /= np.sum(prio)
        priobuffer = np.append(priobuffer, prio)
        self.priorities = priobuffer[:, True]


class trainer_config:
    '''
    configuration for the Q learner (trainer) for easy reuse
    everything not model related goes here. maybe 
    '''

    def __init__(self,
                 app_name,
                 BUFFER_SIZE=50e3,
                 STEPS_PER_EPISODE=500,
                 MAX_STEPS=100000,
                 UPDATE_TARGET_STEPS=1000,
                 BATCH_SIZE=32,
                 GAMMA=0.99,
                 EXPLORATION=100,
                 E_MIN=0.01,
                 priority=False,
                 alpha=0.6,
                 epsilon=0.01

                 ):
        ### game environment
        self.app_name = app_name
        # env.close()
        ### training variables
        self.BUFFER_SIZE = BUFFER_SIZE
        self.STEPS_PER_EPISODE = STEPS_PER_EPISODE
        self.MAX_STEPS = MAX_STEPS
        self.UPDATE_TARGET_STEPS = UPDATE_TARGET_STEPS
        self.BATCH_SIZE = BATCH_SIZE
        self.GAMMA = GAMMA
        self.EXPLORATION = EXPLORATION
        self.E_MIN = E_MIN
        #### PRIO MODULE ( default := alpha= 0.,epsilon=0.01)
        self.priority = priority
        self.alpha = alpha
        self.epsilon = epsilon


class trainer:
    '''
    the actual DDQN-> 2 models, 1 config
    train here, get your models and plots
    '''

    def __init__(self, onlineModel, targetModel, trainer_config, env):
        ### load config 
        self.app_name = trainer_config.app_name
        self.env = env

        ### training variables
        self.BUFFER_SIZE = trainer_config.BUFFER_SIZE
        self.STEPS_PER_EPISODE = trainer_config.STEPS_PER_EPISODE
        self.MAX_STEPS = trainer_config.MAX_STEPS
        self.UPDATE_TARGET_STEPS = trainer_config.UPDATE_TARGET_STEPS
        self.BATCH_SIZE = trainer_config.BATCH_SIZE
        self.GAMMA = trainer_config.GAMMA
        self.EXPLORATION = trainer_config.EXPLORATION
        self.E_MIN = trainer_config.E_MIN
        self.priority = trainer_config.priority
        self.alpha = trainer_config.alpha
        self.epsilon = trainer_config.epsilon

        ### models
        self.onlineNet = onlineModel
        self.targetNet = targetModel

        ### logs
        self.reward_plot = []
        self.loss_plot = []
        self.online_q_plot = []
        self.target_q_plot = []

        ### ringbuffer
        self.REPLAY_BUFFER = ringbuffer(self.BUFFER_SIZE)

    # def load_config(self, config):
    #     '''
    #     loads new config
    #     '''
    #     ### env
    #     self.app_name = config.app_name
    #     self.env = AimsunEnv()
    #     ### training variables
    #     self.BUFFER_SIZE = config.BUFFER_SIZE
    #     self.STEPS_PER_EPISODE = config.STEPS_PER_EPISODE
    #     self.MAX_STEPS = config.MAX_STEPS
    #     self.UPDATE_TARGET_STEPS = config.UPDATE_TARGET_STEPS
    #     self.BATCH_SIZE = config.BATCH_SIZE
    #     self.GAMMA = config.GAMMA
    #     self.EXPLORATION = config.EXPLORATION
    #     self.E_MIN = config.E_MIN
    #     self.priority = config.priority
    #     self.alpha = config.alpha
    #     self.epsilon = config.epsilon

    def save_config(self):
        '''
        returns current config
        '''
        return trainer_config(self.app_name,
                              self.BUFFER_SIZE,
                              self.STEPS_PER_EPISODE,
                              self.MAX_STEPS,
                              self.UPDATE_TARGET_STEPS,
                              self.BATCH_SIZE,
                              self.GAMMA,
                              self.EXPLORATION,
                              self.E_MIN,
                              self.priority,
                              self.alpha,
                              self.epsilon
                              )

    def normalize_state(self, state):
        state_buffer = self.REPLAY_BUFFER.state_buffer
        state = np.array(state).reshape(1, len(state))
        if not (state_buffer is None or state_buffer.shape[0] <= 1): 
            mean = np.mean(state_buffer, axis=0)
            std = np.std(state_buffer, axis=0)
            state = np.divide((state - mean), std, out=(state - mean), where=(std!=0))
        return state

    def save_model(self):
        all_attribute = [self.save_config(), 
                         self.env, 
                         self.onlineNet, 
                         self.targetNet, 
                         self.reward_plot, 
                         self.loss_plot, 
                         self.REPLAY_BUFFER,
                         self.target_q_plot,
                         self.online_q_plot]
        is_written = False
        while not is_written:
            try:
                with open(LOG_PATH + 'Model', 'wb') as fout:
                    pickle.dump(all_attribute, fout)
                is_written = True
            except:
                print("Save model failed.")
                return

    def load_model(self, flag=False):
        if flag:
            try:
                # all_attribute = [self.save_config(), self.env, self.onlineNet, self.targetNet,
                #                  self.reward_plot, self.loss_plot, self.REPLAY_BUFFER]
                with open(LOG_PATH + 'Model', 'rb') as fin:
                    all_attribute =  pickle.load(fin)


                if len(all_attribute) != 7:
                    print("Model empty...")
                    pass

                trainer_config = all_attribute[0]
                env = all_attribute[1]
                onlineNet = all_attribute[2]
                targetNet = all_attribute[3]
                reward_plot = all_attribute[4]
                loss_plot = all_attribute[5]
                REPLAY_BUFFER = all_attribute[6]


                self.app_name = trainer_config.app_name
                self.env = env
                ### training variables
                self.BUFFER_SIZE = trainer_config.BUFFER_SIZE
                self.STEPS_PER_EPISODE = trainer_config.STEPS_PER_EPISODE
                self.MAX_STEPS = trainer_config.MAX_STEPS
                self.UPDATE_TARGET_STEPS = trainer_config.UPDATE_TARGET_STEPS
                self.BATCH_SIZE = trainer_config.BATCH_SIZE
                self.GAMMA = trainer_config.GAMMA
                self.EXPLORATION = trainer_config.EXPLORATION
                self.E_MIN = trainer_config.E_MIN
                self.priority = trainer_config.priority
                self.alpha = trainer_config.alpha
                self.epsilon = trainer_config.epsilon

                ### models
                self.onlineNet = onlineNet
                self.targetNet = targetNet

                ### logs
                self.reward_plot = reward_plot
                self.loss_plot = loss_plot

                ### ringbuffer
                self.REPLAY_BUFFER = REPLAY_BUFFER
            except:
                print("Model not found...")
                pass
        else:
            pass

    # def log_weight(self):
    #     onlineFrob = []
    #     targetFrob = []
    #     online = self.onlineNet
    #     target = self.targetNet
    #     for L in range(len(online.Layerlist)):
    #         onlineFrob.append(LA.norm(online.Layerlist[L].w))
    #         targetFrob.append(LA.norm(target.Layerlist[L].w))

    #     with open(online_w, "a+") as online:
    #         csv_write = csv.writer(online, dialect='excel')
    #         csv_write.writerow(onlineFrob)
    #     with open(target_w, "a+") as target:
    #         csv_write = csv.writer(target, dialect='excel')
    #         csv_write.writerow(targetFrob)

    def train(self, flag=False, log=False):
        eps_rew = 0.
        step_counter = 0.
        current_state = self.normalize_state(self.env.reset())

        for STEP in range(self.MAX_STEPS):
            e = 1. / ((len(self.loss_plot) / self.EXPLORATION) + 1)
            if np.random.uniform(0, 1) < max(self.E_MIN, e):
                # random action
                action = self.env.rand_action()

            else:
                Q = (self.onlineNet.infer(current_state))[0]
                action = np.argmax(Q)
            # apply action
            next_state, reward, done = self.env.step(action)
            next_state = self.normalize_state(next_state)

            # end training when simulation ends
            if done: break
            if not self.env.exclude():
                eps_rew += reward
                self.REPLAY_BUFFER.add(
                    [current_state, 
                     np.array(action).reshape(1, 1), 
                     np.array(reward).reshape(1, 1), 
                     next_state, 
                     np.array(done).reshape(1, 1)])
                step_counter += 1.


            if STEP > 2000 or flag:
                BATCH = self.REPLAY_BUFFER.sample(self.BATCH_SIZE, prio=self.priority)
                train_bellman(self.onlineNet, self.targetNet, BATCH, self.GAMMA)
                write_csv(Q_target_log, (self.targetNet.infer(current_state))[0])
                write_csv(Q_online_log, (self.onlineNet.infer(current_state))[0])
                write_csv(Rt_log, [reward])
                write_csv(Loss, [self.onlineNet.loss])
                self.loss_plot += [self.onlineNet.loss]
                self.reward_plot += [eps_rew]

            current_state = next_state

            if (STEP + 1) % self.UPDATE_TARGET_STEPS == 0:
                if self.priority: self.REPLAY_BUFFER.prio_update(self.onlineNet, self.targetNet, GAMMA=self.GAMMA,
                                                                 alpha=self.alpha, epsilon=self.epsilon)
                if log: print('update: ', len(self.reward_plot), ' episodes ---- 2 eps average reward: ',
                              np.array(self.reward_plot)[-2:].mean())
                update_target(self.onlineNet, self.targetNet, duel=False)

            # self.log_weight()
            if STEP % 10 == 0: self.save_model()



