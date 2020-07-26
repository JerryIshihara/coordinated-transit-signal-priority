class BusInPOZ:
    
    def __init__(self, intersection, check_in_bus_info, check_in_phase, check_in_phasetime, check_in_time, last_check_in=0):
        self.intersection_of_interest = intersection
        self.bus_id = check_in_bus_info.idVeh
        self.check_in_time = check_in_time
        self.check_in_phase = check_in_phase
        self.check_in_phasetime = check_in_phasetime

        self.check_in_headway = check_in_time - last_check_in

        self.check_out_time = -1
        self.check_out_headway = -1

        self.last_update_time = check_in_time

    def check_out(self, check_out_time, last_check_out=0):
        self.check_out_time = check_out_time
        self.check_out_headway = last_check_out - check_out_time
        self.last_update_time = check_out_time