"""Utility functions
"""



def get_phase_number(total_number_of_phases, phase_number):
    """Summary
    
    Parameters
    ----------
    total_number_of_phases : TYPE
        Description
    phase_number : TYPE
        Description
    
    Returns
    -------
    TYPE
        Description
    """
    # wrap around the phases (use this to find phase after last phase or before phase 1)
    while phase_number <= 0:
        phase_number += total_number_of_phases
    while phase_number > total_number_of_phases:
        phase_number -= total_number_of_phases
    return phase_number


def time_to_phase_end(phase_duration, phase):
    """Summary
    
    Parameters
    ----------
    phase_duration : TYPE
        Description
    phase : TYPE
        Description
    
    Returns
    -------
    TYPE
        Description
    """
    return sum(phase_duration[:phase]
               ) if phase != len(phase_duration) else sum(phase_duration)