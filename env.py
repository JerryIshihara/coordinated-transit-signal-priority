"""
A class that creates functionally that the enviroment must have
"""
import numpy as np
import random
from config import *


class Environment():
    
    """
    Attributes:
        ACTION_LOG (str): file path to the textfile that records the chosen action at every time step
                            action_space (List[(int, int)]): a set of possible actions
        debug (bool): 
        env_name (str): name of this environment
        STATE_LOG (str): file path to the textfile that records the states (collected when time steps are renewed)
    """
    
    def __init__(self, debug=False, name, action_space):
        """
        Initialize an environment object
        
        Args:
            debug (bool, optional): 
            name (str): name of the initialized environment
            action_space (List[(int, int)]): a set of possible actions 
        """
        self.env_name = name
        self.debug = debug
        self.action_space = action_space
        self.STATE_LOG = STATE
        self.ACTION_LOG = ACTION

    def step(self, action_index):
        """
        steps return, called when apply actions. Returns the next state, reward, and two 
        booleans indicating whether the simulation ends and whether the episode is done
        
        Args:
            action_index (int): the action index is equal to argmax Q, and will 
                                    use the index to obtain the action from the action space
        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    def reset(self):
        """
        Begin the episode with a random state
        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    def rand_action(self):
        """
        Choose an action randomly (exploring)
        Returns:
            int: index of a random action drew from the action space
        """
        return np.random.randint(0, len(self.action_space))


