from AAPI import *
import csv

CWD = 'C:/Users/Public/Documents/ShalabyGroup/aimsun_ddqn_server/log_files/'
TransferToDQN = CWD + 'TransferToDQN.txt'
TransferToAimsun = CWD + 'TransferToAimsun.txt'
Scenario_End = CWD + 'Scenario_End.txt'
Num_bus_in_rep = CWD + 'Num_bus_in_rep.txt'
Parameter_log = CWD + 'Parameter_log.csv'
Temp_Reward = CWD + 'Temp_Reward.txt'

# configuration of intersection 1
CONFIG_1 = {
    'intersection': 1171274,
    'busCallDetector': 1171405,
    'busExitDetector': 1171391,
    'section': 6601,
    'phase_duration': [16, 38, 7, 11, 32, 6],
    'phase_of_interest': 5,
    'target_headway': 290
}

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
        
        self.busintime_list = [0, 0]
        self.busoutime_list = [0, 0]

        self.states = []
        self.tToNearGreenPhase_list = []
        self.allnumvel_list = []
        self.check_in_hdy_L = []
        self.check_in_phase_no_L = []
        self.check_in_phaseTime_L = []

    def log_parameter_file(self, bus_info, phasetime):
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

        # >>>>>>>>>>>>>>>>> reward <<<<<<<<<<<<<<<
        # reward
        # Travel time

        # reward = []
        # while len(reward) == 0:
        #     try:
        #         f = open(Temp_Reward, "r")
        #         reward = float(f.read())
        #         f.close()
        #     except:
        #         continue

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

        with open(Parameter_log, "a+") as out:  # Log key parameters
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

        tToNearGreenPhase_list = self.tToNearGreenPhase_list
        allnumvel_list = self.allnumvel_list

        # >>>>>>>>>>>>>>>>> check in info <<<<<<<<<<<<<
        busintime_list = self.busintime_list
        check_in_hdy_L = self.check_in_hdy_L
        check_in_phase_no_L = self.check_in_phase_no_L
        check_in_phaseTime_L = self.check_in_phaseTime_L
        # >>>>>>>>>>>>>>>>> check out info <<<<<<<<<<<<<
        busoutime_list = self.busoutime_list

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
                    self.numbus += 1
                    self.allnumvel += 1

                    # log info
                    busintime_list.append(time)
                    check_in_hdy_L.append(busintime_list[-1] - busintime_list[-2])
                    check_in_phase_no_L.append(currentPhase)
                    check_in_phaseTime_L.append(phasetime)

                    extended = self.red_extend + self.green_extend
                    tToNearGreenPhase = self.get_toNearGreenPhase(currentPhase, phasetime, extended)

                    if self.numbus > 1:
                        tToNearGreenPhase_list.append(tToNearGreenPhase)
                        allnumvel_list.append(self.allnumvel)

                    if self.numbus == 1:
                        tt_target = busoutime_list[-1] - busintime_list[-1]

                        # Update states
                        self.updated = -self.updated
                        output = [tt_target, tToNearGreenPhase, self.allnumvel, busoutime_list[-2], busoutime_list[-1],
                                  busoutime_list[-1] - busintime_list[-2], self.remain, busintime_list[-3],
                                  busintime_list[-2], self.updated]

                        # output to DQN
                        print("Output: {}".format(output))
                        f = open(TransferToDQN, "w+")
                        for j in output:
                            f.write("%f " % j)
                        f.close()

                        # log states
                        self.states.append([tt_target, tToNearGreenPhase, self.allnumvel])

                        # Extend the phase for extended time
                        extend_green_phase(time, timeSta, currentPhase, phasetime, False, self)

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

                    busoutime_list.append(time)

                    travelTime = busoutime_list[-1] - busintime_list[-2] if self.numbus >= 1 else busoutime_list[-1] - \
                                                                                             busintime_list[-1]

                    ##### log #########
                    self.log_parameter_file(busout_info, phasetime)
                    ###### log #######

                    print("red_extend: {}".format(self.red_extend))
                    print("green_extend: {}".format(self.green_extend))
                    print("Green phase remaining at exit: {}".format(self.remain))

                    if self.numbus >= 1:
                        tt_target = busoutime_list[-1] - busintime_list[-1]

                        # Update states
                        self.updated = -self.updated
                        output = [tt_target, tToNearGreenPhase_list[0], allnumvel_list[0] - 1, busoutime_list[-2],
                                  busoutime_list[-1],
                                  busoutime_list[-1] - busintime_list[-2], self.remain, busintime_list[-3],
                                  busintime_list[-2], self.updated]
                        print("Output: {}".format(output))
                        f = open(TransferToDQN, "w+")
                        for j in output:
                            f.write("%f " % j)
                        f.close()

                        # log states
                        self.states.append([tt_target, tToNearGreenPhase_list[0], allnumvel_list[0] - 1])

                        tToNearGreenPhase_list.pop(0)
                        allnumvel_list.pop(0)

                        # extend green phase
                        extend_green_phase(time, timeSta, currentPhase, phasetime, True, self)

            self.last_out_info = temp_info.idVeh

        if len(busoutime_list) > 10 and len(busintime_list) > 10:
            self.busoutime_list = busoutime_list[6:]
            self.busintime_list = busintime_list[6:]

        return 0


def AAPILoad():
    # global numbus
    # # global enterNum_record
    # global total_bus
    # global cycled_bus
    # global last_input_flag
    # global allnumvel  # number of all vehicles (cars and buses) between bus call and exit detector
    # global last_in_info
    # global last_out_info
    # global last_allin_info
    # global last_allout_info
    # global updated
    # global time_when_extend
    # global last_Phase
    # global starttime_phase
    # global green_start_time

    global intx_1
    intx_1 = Intersection(CONFIG_1)

    ########################## for log purpose #######################
    # replicationID (exit)
    # vehicleID (exit)
    # >>>>>>>>>>>>>>>>> state <<<<<<<<<<<<<<<
    # global states
    #
    # states = []

    # global action
    # global red_extend  # duration (sec) of green phase extension or reduction
    # global green_extend
    # global remain
    # action = 0
    # red_extend, green_extend = 0, 0
    # remain = 0

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


def extend_green_phase(time, timeSta, currentPhase, phasetime, two_bus_poz, intx):
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
            red_green = int(input_fromDQN[0])
            duration = int(input_fromDQN[1])
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


