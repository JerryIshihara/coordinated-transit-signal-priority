"""configuration for the project

Attributes
----------
CONFIG_1 : str
    the meta data of each intersection
CONFIG_2 : str
    the meta data of each intersection
CORRIDOR : list
    the corridor for training
CWD : str
    the project directory
LOG_PATH : str
    log files folder
"""

import os, inspect, shutil

CWD = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOG_PATH = CWD + '/log_files/'

# log files
STATE = LOG_PATH + 'state.txt'
ACTION = LOG_PATH + 'action.txt'
REWARD = LOG_PATH + 'reward.txt'
REWARD_CSV = LOG_PATH + 'reward_log.csv'
PARAMETER_LOG = LOG_PATH + 'parameter_log.csv'
Num_bus_in_rep = LOG_PATH + 'Num_bus_in_rep.txt'


def clean_folder_and_initialize():
    folder = LOG_PATH
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    os.makedirs(LOG_PATH, exist_ok=True)
    with open(PARAMETER_LOG, 'w+') as log_file:
        log_file.write('log, replication ID, vehicle ID, checkin time, checkout time, check in phase number, check in phase time, checkout phase time, checkin headway, checkout headway, action 1, action 2 as decided at the bus check in, registered action at bus check out, Travel time, reward, prePOZ bus checkout time, prePOZ numbus, last_available_checkout_time, last_check_in_time, check_in_hdy, numbus, allnumvel, tToNearGreenPhase, prePOZ bus checkout time, prePOZ numbus, last_available_checkout_time, last_check_in_time, check_in_hdy, numbus, allnumvel, tToNearGreenPhase\n')


INTERSECTION_1 = {
    'corridor_log': PARAMETER_LOG,
    'intersection': 1171274,
    'busCallDetector': 1171405,
    'busExitDetector': 1171391,
    'section': 6601,
    'phase_duration': [16, 38, 7, 11, 32, 6],
    'phase_of_interest': 5,
    'AlgB_decision': 9,
    'log': LOG_PATH + '1171274.csv',
    'target_headway': 290,
    'prePOZ': {
        'busExitDetector': 1171393,
        'busCallDetector': 1171405,
    },
    'maxTT': 400

}
INTERSECTION_2 = {
    'corridor_log': PARAMETER_LOG,
    'intersection': 1171288,
    'busCallDetector': 1171407,
    'busExitDetector': 1171389,
    'section': 6563,
    'phase_duration': [38, 8, 13, 4, 40, 7],
    'phase_of_interest': 5,
    'AlgB_decision': 12,
    'log': LOG_PATH + '1171288.csv',
    'target_headway': 290,
    'prePOZ': {
        'busExitDetector': 1171391,
        'busCallDetector': 1171407,
    },
    'maxTT': 200
}


CORRIDOR = [INTERSECTION_1, INTERSECTION_2]

