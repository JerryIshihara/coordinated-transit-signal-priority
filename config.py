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

LOG_PATH = CWD + 'log_files/'


# log files
STATE = LOG_PATH + 'STATE.txt'
ACTION = LOG_PATH + 'ACTION.txt'
Scenario_End = LOG_PATH + 'Scenario_End.txt'
Reward_log = LOG_PATH + 'Reward.csv'
Temp_Reward = LOG_PATH + 'Temp_Reward.txt'
Num_bus_in_rep = LOG_PATH + 'Num_bus_in_rep.txt'


INTERSECTION_1 = {
    'intersection': 1171288,
    'busCallDetector': 1171407,
    'busExitDetector': 1171389,
    'section': 6563,
    'phase_duration': [38, 8, 13, 4, 40, 7],
    'phase_of_interest': 5,
    'AlgB_decision': 12,
    'log': LOG_PATH + '1171288.csv',
    'target_headway': 290
}

INTERSECTION_2 = {
    'intersection': 1171274,
    'busCallDetector': 1171405,
    'busExitDetector': 1171391,
    'section': 6601,
    'phase_duration': [16, 38, 7, 11, 32, 6],
    'phase_of_interest': 5,
    'AlgB_decision': 9,
    'log': LOG_PATH + '1171274.csv',
    'target_headway': 290
}

CORRIDOR = [INTERSECTION_1, INTERSECTION_2]