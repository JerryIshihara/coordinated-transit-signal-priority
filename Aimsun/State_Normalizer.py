"""State Normalizer
"""
import numpy as np

class State_Normalizer():
    
    """
    Note that Welford's online algorithm are used to perform the calculations
    
    Attributes
    ----------
    num_recorded_states:
        state count
    mean:
        mean of each observations
    var:
        sample variance of each observations
    mean_diff
        will be used to calculate the sample variance 
    """
    
    def __init__(self, state_len):
        
        self.num_recorded_states = np.zeros(state_len)
        self.mean = np.zeros(state_len)
        self.mean_diff = np.zeros(state_len)
        self.var = np.zeros(state_len)

    def observe(self, new_state)

        """Called when a new state is collected, update the attributes of the normalizer
        
        Parameters
        ----------
        new_state : List
            List of observations of the new state
        """
        
        new_state_arr = np.array(new_state)
        self.num_recorded_states = self.num_recorded_states + 1
        last_mean = np.copy(self.mean)
        self.mean += (new_state-self.mean)/self.num_recorded_states
        self.mean_diff += (new_state-last_mean)*(new_state-self.mean)
        self.var = self.mean_diff/(self.num_recorded_states-1)
        
    def normalize(self, state):
        
        """Called when sending a state to DQN, normalize the states
        
        Parameters
        ----------
        state : List
            List of observations of the new state
            
        Returns
        -------
        List of observations of a normalized state
        """
        
        state_arr = np.array(state)
        std = np.sqrt(self.var)
        return ((state-self.mean)/std).tolist()
        
        
        
        
        
        