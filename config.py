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

import os, inspect

CWD = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOG_PATH = CWD + '/log_files/'

# log files
STATE = LOG_PATH + 'state.txt'
ACTION = LOG_PATH + 'action.txt'
REWARD = LOG_PATH + 'reward.txt'
REWARD_CSV = LOG_PATH + 'reward_log.csv'
PARAMETER_LOG = LOG_PATH + 'parameter_log.csv'
Num_bus_in_rep = LOG_PATH + 'Num_bus_in_rep.txt'

INTERSECTION_1 = {
    'intersection': 1171274,
    'busCallDetector': 1171405,
    'busExitDetector': 1171391,
    'section': 6601,
    'phase_duration': [12, 4, 38, 7, 7, 4, 32, 6],
    'phase_of_interest': 5,
    'AlgB_decision': 9,
    'log': LOG_PATH + '1171274.csv',
    'target_headway': 290,
    'prePOZ': {
        'busExitDetector': 1171393,
        'busCallDetector': 1171405,
    }

}
INTERSECTION_2 = {
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
    }
}


CORRIDOR = [INTERSECTION_1, INTERSECTION_2]