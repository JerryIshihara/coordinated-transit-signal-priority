from modules import ddqn_framework as ddqn
from modules import mlp_framework as nn
import pickle

CWD = 'D:\AimSun Python\aimsun_ddqn_server\log_files\\'

# STEP 1: create configuration
if __name__ == '__main__':
    configuration = ddqn.trainer_config(app_name='AimsunNext',
                                        BUFFER_SIZE=50e3,
                                        # STEPS_PER_EPISODE = 500,
                                        STEPS_PER_EPISODE=5,
                                        MAX_STEPS=9999999,
                                        # UPDATE_TARGET_STEPS = 1000,
                                        UPDATE_TARGET_STEPS=10,
                                        BATCH_SIZE=32,
                                        GAMMA=0.9,
                                        EXPLORATION=100,
                                        E_MIN=0.01,
                                        priority=False,
                                        alpha=0.001,
                                        epsilon=0.1
                                        )

    # STEP 2: build models (online & target)
    A1 = nn.layer(configuration.INPUT_SIZE, nodes=16)
    A1.f = nn.f_relu  # relu for activation
    A2 = nn.layer(16, 16)
    A2.f = nn.f_relu  # relu for activation
    AOUT = nn.layer(16, configuration.OUTPUT_SIZE)
    AOUT.f = nn.f_relu

    L1 = nn.layer(configuration.INPUT_SIZE, nodes=16)
    L1.f = nn.f_relu  # relu for activation
    L2 = nn.layer(16, 16)
    L2.f = nn.f_relu  # relu for activation
    LOUT = nn.layer(16, configuration.OUTPUT_SIZE)
    LOUT.f = nn.f_relu
    onlineNet = nn.mlp([A1, A2, AOUT])
    onlineNet.erf = nn.reduce_mean_sqr_error  # cost in prev aimsun_dqn
    targetNet = nn.mlp([L1, L2, LOUT])
    targetNet.erf = nn.reduce_mean_sqr_error  # cost in prev aimsun_dqn

    # STEP 3: create trainer
    ddqn_model = ddqn.trainer(onlineNet, targetNet, configuration)

    # STEP 5: train the trainer (dqn_model) for configuration.MAX_STEPS:
    ddqn_model.train(log=True)

    # store the whole class as training finished
    with open(CWD + 'Model.txt', 'wb') as fout:
        pickle.dump(ddqn_model, fout)

    print('\n' + 'training done')
    # OR: train the trainer (dqn_model) for one episode(!) by setting 'flag' = True :
    # ddqn_model.train(flag=True)

#  STEP 6:
# get your models, config and logs from the trainer (see 'some useful stuff')

#################### some usefull stuff:
### save config
# first_config = dqn_model.save_config()
### use new config ('new_config')
# dqn_model.load_config(new_config)
### apply/get  model
# dqn_model.onlineNet = new_onlineNet
# trained_targetNet  = dqn_model.targetNet
### clear REPLAY BUFFER
# dqn_model.REPLAY_BUFFER = DDQN.ringbuffer(dqn_model.BUFFER_SIZE)
### get reward / loss logs
# loss_list = dqn_model.loss_plot
# reward_list = dqn_model.reward_plot