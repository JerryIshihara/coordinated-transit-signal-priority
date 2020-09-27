class BusInPOZ:
    
    def __init__(self, intersection, check_in_bus_info, check_in_phase, check_in_phasetime, check_in_time, last_check_in):
        self.intersection_of_interest = intersection
        self.bus_id = check_in_bus_info.idVeh
        self.check_in_time = check_in_time
        self.check_in_phase = check_in_phase
        self.check_in_phasetime = check_in_phasetime
        self.last_check_in = last_check_in # previous bus check in time

        self.check_in_headway = check_in_time - last_check_in

        self.check_out_time = -1
        self.check_out_headway = -1

        self.last_update_time = check_in_time
        self.original_action = None
        self.original_state = None # state generated at check in

    def check_out(self, check_out_time, last_check_out=0):
        self.check_out_time = check_out_time
        self.check_out_headway = check_out_time - last_check_out
        self.last_update_time = check_out_time

    def set_action(self, action):
        if self.original_action is None:
            self.original_action = action
        else:
            print("duplicate set original action, check to make sure implementation is correct")

    def set_state(self, state):
        if self.original_state is None:
            self.original_state = state
        else:
            print("duplicate set original state, check to make sure implementation is correct")
