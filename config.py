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

CWD = 'C:/Users/Public/Documents/ShalabyGroup/tsp_base_b_2intx/'

LOG_PATH = CWD + 'log_files/'

INTERSECTION_1 = {
    'intersection': 1171288,
    'busCallDetector': 1171407,
    'busExitDetector': 1171389,
    'section': 6563,
    'phase_duration': [38, 8, 13, 4, 40, 7],
    'phase_of_interest': 5,
    'AlgB_decision': 12,
    'log': LOG_PATH + '1171288.csv'
}

INTERSECTION_2 = {
    'intersection': 1171274,
    'busCallDetector': 1171405,
    'busExitDetector': 1171391,
    'section': 6601,
    'phase_duration': [16, 38, 7, 11, 32, 6],
    'phase_of_interest': 5,
    'AlgB_decision': 9,
    'log': LOG_PATH + '1171274.csv'
}

CORRIDOR = []