"""Summary
"""
import numpy as np
import random
from config import *


class Environment:
    """Summary
    
    Attributes:
        ACTION_LOG (TYPE): Description
        action_space (TYPE): Description
        env_name (TYPE): Description
        STATE_LOG (TYPE): Description
    """
    
    def __init__(self, name, action_space):
        """Summary
        
        Args:
            name (TYPE): Description
            action_space (TYPE): Description
        """
        self.env_name = name
        self.action_space = action_space
        self.STATE_LOG = STATE
        self.ACTION_LOG = ACTION

    def step(self, action_index):
        """Summary
        
        Args:
            action_index (int): Description
        
        Raises:
            NotImplementedError: Description
        """
        raise NotImplementedError

    def reset(self):
        """Summary
        
        Raises:
            NotImplementedError: Description
        """
        raise NotImplementedError

    def rand_action(self):
        """Summary
        
        Returns:
            TYPE: Description
        """
        return np.random.randint(0, len(self.action_space))


