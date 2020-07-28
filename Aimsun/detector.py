from AAPI import *
import os, sys, inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from config import *
import csv

TransferToDQN = LOG_PATH + 'TransferToDQN.txt'
TransferToAimsun = LOG_PATH + 'TransferToAimsun.txt'
Scenario_End = LOG_PATH + 'Scenario_End.txt'
Num_bus_in_rep = LOG_PATH + 'Num_bus_in_rep.txt'
# Parameter_log = LOG_PATH + 'Parameter_log.csv'
Temp_Reward = LOG_PATH + 'Temp_Reward.txt'

# =============== util =====================


def time_to_phase_end(phase_duration, phase):
    return sum(phase_duration[:phase]) if phase != len(phase_duration) else sum(phase_duration)


def get_phase_number(total_number_of_phases, phase_number):
    # wrap around the phases (use this to find phase after last phase or before phase 1)
    while phase_number <= 0:
        phase_number += total_number_of_phases
    while phase_number > total_number_of_phases:
        phase_number -= total_number_of_phases
    return phase_number


class Bus_in_POZ:
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


class Intersection:
    def __init__(self, CONFIG):
        self.CONFIG = CONFIG

        self.numbus = 0
        self.total_bus = 0
        self.cycled_bus = 0
        self.last_input_flag = 99
        self.allnumvel = 0
        self.last_in_info = -99
        self.last_out_info = -99
        self.last_allin_info = -99
        self.last_allout_info = -99
        self.updated = 1
        self.time_when_extend = 0
        self.last_Phase = -1
        self.starttime_phase = 0
        self.green_start_time = 0

        self.action = 0
        self.red_extend = 0
        self.green_extend = 0
        self.remain = 0
        self.replicationID = None
        
        # self.busintime_list = [0, 0]
        # self.busoutime_list = [0, 0]

        self.states = []
        # self.tToNearGreenPhase_list = []
        # self.allnumvel_list = []
        # self.check_in_hdy_L = []
        # self.check_in_phase_no_L = []
        # self.check_in_phaseTime_L = []

        self.list_of_bus_in_POZ = []
        self.list_of_bus_checked_out = []
        self.cumulative_reward = 0  # track reward generated between check-in

    def checkout_bus_from_POZ(self, checkout_id, checkout_time):
        # remove bus with corresponding id from POZ and return the bus
        for bus in self.list_of_bus_in_POZ:
            if bus.bus_id == checkout_id:
                if self.list_of_bus_checked_out:
                    last_checkout_time = self.list_of_bus_checked_out[-1].check_out_time
                else:
                    # if there is no previous bus, assume checkout headway is perfect
                    last_checkout_time = checkout_time - self.CONFIG['target_headway']
                bus.check_out(checkout_time, last_checkout_time)
                self.list_of_bus_in_POZ.remove(bus)
                return bus
        return False


    def compute_reward(self, travelTime, bus_object):
        """Summary
        compute reward gained by a newly checked out bus
        """
        d_out = abs(bus_object.check_out_headway-self.CONFIG['target_headway'])
        d_in = abs(bus_object.check_in_headway-self.CONFIG['target_headway'])
        improve = d_in-d_out
        new_reward = 0.6 * improve - 0.4 * travelTime
        return new_reward


    def log_parameter_file(self, bus_info, phasetime):
        ### TODO: finish implement this function using the bus objects
        ############## for log purpose ###############
        replicationID = ANGConnGetReplicationId()
        vehicleID = bus_info.idVeh
        # >>>>>>>>>>>>>>>>> state <<<<<<<<<<<<<<<
        this_states = self.states[0]
        # >>>>>>>>>>>>>>>>> check in info <<<<<<<<<<<<<<<
        busintime_list = self.busintime_list
        check_in_hdy_L = self.check_in_hdy_L
        check_in_phase_no_L = self.check_in_phase_no_L
        check_in_phaseTime_L = self.check_in_phaseTime_L
        # >>>>>>>>>>>>>>>>> check out info <<<<<<<<<<<<<<<
        busoutime_list = self.busoutime_list
        # >>>>>>>>>>>>>>>>> target headway <<<<<<<<<<<<<<<
        target_headway = self.CONFIG['target_headway']

        # >>>>>>>>>>>>>>>>> parameter log file <<<<<<<<<<<<<<<<<
        parameter_log_file = self.CONFIG['log']
        # >>>>>>>>>>>>>>>>> reward <<<<<<<<<<<<<<<

        check_out_hdy = busoutime_list[-1] - busoutime_list[-2]
        travelTime = busoutime_list[-1] - busintime_list[2]
        currentPhase = ECIGetCurrentPhase(1171274)  # get current phase
        # NOTICE: busintime_list[2] can only use index 2 since it could be two buses entered in
        # the same cycle
        output = [replicationID, vehicleID, this_states[0], this_states[1], this_states[2],
                  busintime_list[2], check_in_hdy_L[0], check_in_hdy_L[0] - target_headway, check_in_phase_no_L[0],
                  check_in_phaseTime_L[0],
                  busoutime_list[-1], check_out_hdy, check_out_hdy - target_headway, phasetime,
                  self.action, self.remain, travelTime, currentPhase]

        with open(parameter_log_file, "a+") as out:  # Log key parameters
            csv_write = csv.writer(out, dialect='excel')
            csv_write.writerow(output)

        self.states.pop(0)
        busintime_list.pop(0)
        check_in_hdy_L.pop(0)
        check_in_phase_no_L.pop(0)
        check_in_phaseTime_L.pop(0)
        busoutime_list.pop(0)


    def get_toNearGreenPhase(self, currentPhase, phasetime, extended):
        if currentPhase <= self.CONFIG['phase_of_interest']:
            to_interest = time_to_phase_end(self.CONFIG['phase_duration'], self.CONFIG['phase_of_interest'])
            past_phase = time_to_phase_end(self.CONFIG['phase_duration'], currentPhase - 1)
            return to_interest - phasetime + extended - past_phase
        return sum(self.CONFIG['phase_duration']) - phasetime + extended


    def AAPIPostManage(self, time, timeSta, timeTrans, acycle):
        target_headway = self.CONFIG['target_headway']
        # retrieve intersection info from CONFIG
        intersection = self.CONFIG['intersection']
        busCallDetector = self.CONFIG['busCallDetector']
        busExitDetector = self.CONFIG['busExitDetector']
        section = self.CONFIG['section']
        busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)  # get bus internal position
        self.replicationID = ANGConnGetReplicationId()

        # determine which phase is green in the bus's perspective
        phase_of_interest = self.CONFIG['phase_of_interest']
        total_phases = len(self.CONFIG['phase_duration']) # assumption for this is that all phases has duration defined

        tt_target = 0
        tToNearGreenPhase = 0  # time (>0) to the end of the nearest green phase

        # current phase time
        currentPhase = ECIGetCurrentPhase(intersection)  # get current phase
        if currentPhase != self.last_Phase:
            self.starttime_phase = time  # a change in phase just happened, reset phase start time
            self.last_Phase = currentPhase
        phasetime = time - self.starttime_phase

        # find phase before and after phase of interest
        phase_after_phase_of_interest = get_phase_number(total_phases, phase_of_interest+1)
        phase_before_phase_of_interest = get_phase_number(total_phases, phase_of_interest-1)

        if currentPhase == phase_after_phase_of_interest and phasetime == 0:
            # green phase ended and the buses that are still in POZ becomes cycled buses
            cycled_bus = self.numbus
        if currentPhase != phase_of_interest and (self.numbus - self.cycled_bus == 0):
            self.green_extend = 0
            ECIChangeTimingPhase(intersection, phase_of_interest, self.CONFIG['phase_duration'][phase_of_interest-1], timeSta)
        if currentPhase != 4 and (self.numbus - self.cycled_bus == 0):
            self.red_extend = 0
            ECIChangeTimingPhase(intersection, phase_before_phase_of_interest,  self.CONFIG['phase_duration'][phase_before_phase_of_interest-1], timeSta)

            # Check number of all vehicles in and out
        self.allnumvel = AKIVehStateGetNbVehiclesSection(section, True)

        # bus enter check
        enterNum = AKIDetGetCounterCyclebyId(busCallDetector,
                                             busVehiclePosition)  # Number of entering bus(es) in last step

        new_state = []
        new_bus_entered = False

        if enterNum > 0:
            self.cycled_bus = 0
            self.total_bus += 1

            print("------- No.{} Bus Checked -------".format(self.total_bus))
            print("Number of bus: %d" % enterNum)
            print("Entered at phase: #{}".format(currentPhase))
            print("Phase time: {}".format(phasetime))
            print("Entered at time: {}".format(time))
            print("Bus followed entered %d" % (enterNum - 1))
            # First vehicle info
            busin_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busCallDetector, 0, busVehiclePosition)
            # Last vehicle info
            temp_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busCallDetector, AKIDetGetNbVehsEquippedInDetectionCyclebyId(
                    busCallDetector, busVehiclePosition) - 1, busVehiclePosition)

            is_written = False
            while not is_written:
                try:
                    f = open(Num_bus_in_rep, "w+")
                    f.write("%d " % self.total_bus)
                    f.close()
                    is_written = True
                except:
                    print("failed writing files")
                    continue

            for i in range(enterNum):
                # # Get action from outside

                # If first vehicle equals last vehicle of last step
                if i == 0 and busin_info.idVeh == self.last_in_info:
                    # Skip first vehicle and loop
                    continue
                else:
                    new_bus_entered = True
                    if self.list_of_bus_in_POZ:
                        last_check_in_time = self.list_of_bus_in_POZ[-1].check_in_time
                    else:
                        last_check_in_time = time - target_headway # for the first bus, assume that the check in headway is perfect
                    self.list_of_bus_in_POZ.append(Bus_in_POZ(intersection, busin_info, currentPhase, phasetime, time, last_check_in=last_check_in_time))
                    self.numbus += 1
                    self.allnumvel += 1

                    # !!! do not write to DQN until afterwards
                    # if self.numbus == 1:
                    #     tt_target = busoutime_list[-1] - busintime_list[-1]
                    #
                    #     # Update states
                    #     self.updated = -self.updated
                    #     output = [tt_target, tToNearGreenPhase, self.allnumvel, busoutime_list[-2], busoutime_list[-1],
                    #               busoutime_list[-1] - busintime_list[-2], self.remain, busintime_list[-3],
                    #               busintime_list[-2], self.updated]
                    #
                    #
                    #     # log states
                    #     self.states.append([tt_target, tToNearGreenPhase, self.allnumvel])
                    #
                    #     # Extend the phase for extended time
                    #     # extend_green_phase(time, timeSta, currentPhase, phasetime, False, self)

            self.last_in_info = temp_info.idVeh

        # bus exit check
        exitNum = AKIDetGetCounterCyclebyId(busExitDetector, busVehiclePosition)  # Number of exit vehicle in last step
        if exitNum > 0:
            print("-------- Bus exited %d ---------" % exitNum)
            print("Exited at time: " + str(time))
            # First vehicle info
            busout_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busExitDetector, 0, busVehiclePosition)
            # Last vehicle info
            temp_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busExitDetector, AKIDetGetNbVehsEquippedInDetectionCyclebyId(
                    busExitDetector, busVehiclePosition) - 1, busVehiclePosition)
            for i in range(exitNum):
                # If first vehicle equals last vehicle of last step
                if i == 0 and busout_info.idVeh == self.last_out_info:
                    # Skip first vehicle and loop
                    continue
                else:
                    self.numbus -= 1
                    self.allnumvel -= 1
                    print("Bus banching %d" % self.numbus)
                    checkout_id = busout_info.idVeh
                    checked_out_bus = checkout_bus_from_POZ(checkout_id, time)
                    self.list_of_bus_checked_out.append(checked_out_bus)

                    if checked_out_bus is False:
                        print("Cannot found the bus {} in POZ".format(checkout_id))
                    travelTime = checked_out_bus.check_out_time - checked_out_bus.check_in_time

                    ##### log #########
                    self.log_parameter_file(busout_info, phasetime)
                    ###### log #######

                    print("red_extend: {}".format(self.red_extend))
                    print("green_extend: {}".format(self.green_extend))
                    print("Green phase remaining at exit: {}".format(self.remain))

                    reward_gained = compute_reward(travelTime, checked_out_bus)
                    self.cumulative_reward += reward_gained
                    print("Reward gained at checked out: {}".format(reward_gained))

                    # !!! do not write to DQN for check out
                    # if self.numbus >= 1:
                    #     # tt_target = busoutime_list[-1] - busintime_list[-1]
                    #
                    #     # # Update states
                    #     # self.updated = -self.updated
                    #     # output = [tt_target, tToNearGreenPhase_list[0], allnumvel_list[0] - 1, busoutime_list[-2],
                    #     #           busoutime_list[-1],
                    #     #           busoutime_list[-1] - busintime_list[-2], self.remain, busintime_list[-3],
                    #     #           busintime_list[-2], self.updated]
                    #
                    #
                    #
                    #
                    #
                    #     # # log states
                    #     # self.states.append([tt_target, tToNearGreenPhase_list[0], allnumvel_list[0] - 1])
                    #
                    #     tToNearGreenPhase_list.pop(0)
                    #     allnumvel_list.pop(0)

                        # extend green phase
                        # extend_green_phase(time, timeSta, currentPhase, phasetime, True, self)

            self.last_out_info = temp_info.idVeh

        extended = self.red_extend + self.green_extend
        tToNearGreenPhase = self.get_toNearGreenPhase(currentPhase, phasetime, 0)
        if tToNearGreenPhase <0:
            # already in an extended green phase
            tToNearGreenPhase = 0

        if self.numbus>0:
            # last available checkout for this intersection
            if self.numbus > 1:
                # bunch, use current time as last checkout
                last_available_checkout_time = time
            elif len(self.list_of_bus_checked_out) == 0:
                # first bus
                last_available_checkout_time = time - self.CONFIG['target_headway']
            else:
                last_available_checkout_time = self.list_of_bus_checked_out[-1].check_out_time
            # check in time of the last bus checked in
            last_check_in_time = self.list_of_bus_in_POZ[-1].check_in_time
            check_in_hdy = self.list_of_bus_in_POZ[-1].check_in_headway
            new_state = [last_available_checkout_time, last_check_in_time, check_in_hdy, self.numbus, self.allnumvel, tToNearGreenPhase]
        else:
            new_state = [0, 0, 0, 0, 0, 0]

        if len(self.list_of_bus_checked_out) > 10:
            self.list_of_bus_checked_out = self.list_of_bus_checked_out[-6:]

        return new_bus_entered, new_state


def AAPIPostManage(time, timeSta, timeTrans, acycle):
    # This could be handled by a corridor but i am testing with one intersection first
    global intx_1
    # global intx_2
    new_time_step_1, new_state_1 = intx_1.AAPIPostManage(time, timeSta, timeTrans, acycle)
    if new_time_step_1:
        reward_1 = intx_1.cumulative_reward
        intx_1.cumulative_reward = 0
        #TODO: write the new state and reward calculated to DQN



    return 0


class Corridor:
    def __init__(self, config_list):
        self.intersection_list = []
        for config in config_list:
            self.intersection_list.append(Intersection(INTERSECTION_1))




def AAPILoad():
    #create intersection object

    global intx_1
    # global intx_2
    intx_1 = Intersection(INTERSECTION_1)
    # intx_2 = Intersection(INTERSECTION_2)

    return 0



def AAPIInit():
    ANGConnEnableVehiclesInBatch(True)
    is_written = False
    while not is_written:
        try:
            f = open(Scenario_End, "w+")
            f.write("%d " % 0)
            f.close()
            is_written = True
        except:
            print("failed writing files")
            continue

    is_written = False
    while not is_written:
        try:
            f = open(Num_bus_in_rep, "w+")
            f.write("%d " % 0)
            f.close()
            is_written = True
        except:
            print("failed writing files")
            continue
    return 0


def AAPIManage(time, timeSta, timeTrans, acycle):
    return 0    


def extend_green_phase(time, timeSta, currentPhase, phasetime, two_bus_poz, intx, action_index=(0,1)):

    intersection = intx.CONFIG['intersection']
    phase_of_interest = intx.CONFIG['phase_of_interest']
    total_phases = len(intx.CONFIG['phase_duration'])
    phase_before_phase_of_interest = get_phase_number(total_phases, phase_of_interest-1)

    input_fromDQN = [0]
    while len(input_fromDQN) == 1:
        try:
            f = open(TransferToAimsun, "r")
            input_fromDQN = f.read()
            f.close()
            input_fromDQN = input_fromDQN.split()
        except:
            continue

        if len(input_fromDQN) != 0 and int(input_fromDQN[-1]) != intx.last_input_flag:
            red_green = int(input_fromDQN[action_index[0]])
            duration = int(input_fromDQN[action_index[1]])
            if red_green == -1:
                intx.red_extend += duration
                
            else:
                intx.green_extend += duration

                intx.last_input_flag = int(input_fromDQN[-1])
        else:
            input_fromDQN = [0]

    red_duration = intx.CONFIG['phase_duration'][phase_before_phase_of_interest-1]
    green_duration = intx.CONFIG['phase_duration'][phase_of_interest-1]
    ECIChangeTimingPhase(intersection, phase_before_phase_of_interest, red_duration + intx.red_extend, timeSta)
    ECIChangeTimingPhase(intersection, phase_of_interest, green_duration + intx.green_extend, timeSta)

    print("------- Extend start here ----------")
    print("Extended at time: {}".format(time))
    print("Extended at phase: #{}".format(currentPhase))
    print("Phase Time: {}".format(phasetime))
    print("Red/Green: {}".format("green" if red_green == 1 else "red"))
    print("Extended length: " + str(intx.green_extend if red_green == 1 else intx.red_extend) + " sec")

    intx.time_when_extend = time
    intx.action = (red_green, duration)


def AAPIFinish():
    is_written = False
    while not is_written:
        try:
            f = open(Scenario_End, "w+")
            f.write("%d " % 1)
            f.close()
            is_written = True
        except:
            print("failed writing files")
            continue
    return 0


def AAPIUnLoad():
    return 0


