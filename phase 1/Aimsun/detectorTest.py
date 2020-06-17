from AAPI import *
import csv

CWD = 'C:/Users/Public/Documents/ShalabyGroup/aimsun_ddqn_server/log_files/'
TransferToDQN = CWD + 'TransferToDQN.txt'
TransferToAimsun = CWD + 'TransferToAimsun.txt'
Scenario_End = CWD + 'Scenario_End.txt'
Num_bus_in_rep = CWD + 'Num_bus_in_rep.txt'
Parameter_log = CWD + 'Parameter_log.csv'
Temp_Reward = CWD + 'Temp_Reward.txt'



def log_parameter_file(bus_info, phasetime):
    ############## for log purpose ###############
    replicationID = ANGConnGetReplicationId()
    vehicleID = bus_info.idVeh
    # >>>>>>>>>>>>>>>>> state <<<<<<<<<<<<<<<
    global states
    # tt_target
    # tToNearGreenPhase
    # allnumvel
    this_states = states[0]
    # >>>>>>>>>>>>>>>>> check in info <<<<<<<<<<<<<<<
    global busintime_list
    global check_in_hdy_L
    global checkin_hdy_dev
    global check_in_phase_no_L
    global check_in_phaseTime_L
    # >>>>>>>>>>>>>>>>> check out info <<<<<<<<<<<<<<<
    global butoutime_list
    # check_out_hdy
    # checkout_hdy_dev
    # check_out_phaseTime
    # >>>>>>>>>>>>>>>>> action <<<<<<<<<<<<<<<
    global action
    global remain
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

    check_out_hdy = butoutime_list[-1] - butoutime_list[-2]
    travelTime = butoutime_list[-1] - busintime_list[2]
    currentPhase = ECIGetCurrentPhase(1171274)  # get current phase
    # NOTICE: busintime_list[2] can only use index 2 since it could be two buses entered in 
    # the same cycle
    output = [replicationID, vehicleID, this_states[0], this_states[1], this_states[2],
              busintime_list[2], check_in_hdy_L[0], check_in_hdy_L[0] - 290, check_in_phase_no_L[0], check_in_phaseTime_L[0],
              butoutime_list[-1], check_out_hdy, check_out_hdy - 290, phasetime,
              action, remain, travelTime, currentPhase]


    with open(Parameter_log, "a+") as out:  # Log key parameters
        csv_write = csv.writer(out, dialect='excel')
        csv_write.writerow(output)

    states.pop(0)
    busintime_list.pop(0)
    check_in_hdy_L.pop(0)
    check_in_phase_no_L.pop(0)
    check_in_phaseTime_L.pop(0)
    butoutime_list.pop(0)



def AAPILoad():
    global numbus
    # global enterNum_record
    global total_bus
    global cycled_bus
    global last_input_flag
    global allnumvel  # number of all vehicles (cars and buses) between bus call and exit detector
    global last_in_info
    global last_out_info
    global last_allin_info
    global last_allout_info
    global updated
    global time_when_extend
    global last_Phase
    global starttime_phase
    global green_start_time



    ########################## for log purpose #######################
    # replicationID (exit)
    # vehicleID (exit)
    # >>>>>>>>>>>>>>>>> state <<<<<<<<<<<<<<<
    global states
    # tt_target
    # tToNearGreenPhase
    # allnumvel
    states = []
    # >>>>>>>>>>>>>>>>> check in info <<<<<<<<<<<<<
    global busintime_list
    global check_in_hdy_L
    global checkin_hdy_dev
    global check_in_phase_no_L
    global check_in_phaseTime_L
    busintime_list = [0, 0]
    check_in_hdy_L = []
    check_in_phase_no_L = []
    check_in_phaseTime_L = []
    # >>>>>>>>>>>>>>>>> check out info <<<<<<<<<<<<<
    global butoutime_list
    # check_out_hdy
    # checkout_hdy_dev
    # check_out_phaseTime
    butoutime_list = [0, 0]
    # >>>>>>>>>>>>>>>>> action <<<<<<<<<<<<<<<
    global action
    global red_extend  # duration (sec) of green phase extension or reduction
    global green_extend
    global remain
    action = 0
    red_extend, green_extend = 0, 0
    remain = 0
    # >>>>>>>>>>>>>>>>> reward <<<<<<<<<<<<<<<
    # reward
    # Travel time


    # record 2nd bus when there are 2 buses in POZ
    global tToNearGreenPhase_list
    global allnumvel_list

    tToNearGreenPhase_list = []
    allnumvel_list = []   

    
    # busintime_list = [0, 0]
    # butoutime_list = [0, 0]
    numbus = 0
    # enterNum_record = 0
    total_bus = 0
    cycled_bus = 0
    last_input_flag = 99
    allnumvel = 0
    last_in_info = -99
    last_out_info = -99
    last_allin_info = -99
    last_allout_info = -99
    updated = 1
    time_when_extend = 0
    last_Phase = -1
    starttime_phase = 0
    green_start_time = 0
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



def extend_green_phase(time, timeSta, currentPhase, phasetime, two_bus_poz):
    intersection = 1171274
    global time_when_extend
    global last_input_flag
    global action
    global green_extend
    global red_extend

    input_fromDQN = [0]
    while len(input_fromDQN) == 1:
        try:
            f = open(TransferToAimsun, "r")
            input_fromDQN = f.read()
            f.close()
            input_fromDQN = input_fromDQN.split()
        except:
            continue

        if len(input_fromDQN) != 0 and int(input_fromDQN[-1]) != last_input_flag:
            red_green = int(input_fromDQN[0])
            duration = int(input_fromDQN[1])
            if red_green == -1:
                red_extend += duration
                
            else:
                green_extend += duration

            last_input_flag = int(input_fromDQN[-1])
        else:
            input_fromDQN = [0]


    ECIChangeTimingPhase(intersection, 4, 11 + red_extend, timeSta)
    ECIChangeTimingPhase(intersection, 5, 32 + green_extend, timeSta)

    print("------- Extend start here ----------")
    print("Extended at time: {}".format(time))
    print("Extended at phase: #{}".format(currentPhase))
    print("Phase Time: {}".format(phasetime))
    print("Red/Green: {}".format("green" if red_green == 1 else "red"))
    print("Extended length: " + str(green_extend if red_green == 1 else red_extend) + " sec")

    time_when_extend = time
    action = (red_green, duration)


def AAPIPostManage(time, timeSta, timeTrans, acycle):
    intersection = 1171274
    busCallDetector = 1171405
    busExitDetector = 1171391
    section = 6601
    busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)  # get bus internal position
    global numbus

    # global  enterNum_record
    global total_bus
    global cycled_bus

    global last_input_flag
    global allnumvel
    global last_in_info
    global last_out_info
    global last_allin_info
    global last_allout_info
    global updated
    global time_when_extend
    global last_Phase
    global starttime_phase
    global green_start_time
    global tToNearGreenPhase_list
    global allnumvel_list

    ########################## for log purpose #######################
    # replicationID (exit)
    # vehicleID (exit)
    # >>>>>>>>>>>>>>>>> state <<<<<<<<<<<<<<<
    global states
    # tt_target
    # tToNearGreenPhase
    # allnumvel
    # >>>>>>>>>>>>>>>>> check in info <<<<<<<<<<<<<
    global busintime_list
    global check_in_hdy_L
    global checkin_hdy_dev
    global check_in_phase_no_L
    global check_in_phaseTime_L
    # >>>>>>>>>>>>>>>>> check out info <<<<<<<<<<<<<
    global butoutime_list
    # check_out_hdy
    # checkout_hdy_dev
    # check_out_phaseTime
    # >>>>>>>>>>>>>>>>> action <<<<<<<<<<<<<<<
    # action
    global red_extend
    global green_extend
    global remain
    # >>>>>>>>>>>>>>>>> reward <<<<<<<<<<<<<<<
    # reward
    # Travel time







    tt_target = 0
    tToNearGreenPhase = 0  # time (>0) to the end of the nearest green phase

    # current phase time
    currentPhase = ECIGetCurrentPhase(intersection)  # get current phase
    if currentPhase != last_Phase:
        starttime_phase = time
        last_Phase = currentPhase
    phasetime = time - starttime_phase
    # if currentPhase == 5:
    #     print(phasetime)
    # reset phase-5 green phase to default value
    if currentPhase == 6 and phasetime == 0:
        cycled_bus = numbus
    if currentPhase != 5 and (numbus - cycled_bus == 0):
        green_extend = 0
        ECIChangeTimingPhase(intersection, 5, 32, timeSta)
    if currentPhase != 4 and (numbus - cycled_bus == 0):
        red_extend = 0
        ECIChangeTimingPhase(intersection, 4, 11, timeSta)   
       

    # Check number of all vehicles in and out
    allnumvel = AKIVehStateGetNbVehiclesSection(section, True)

    # bus enter check
    enterNum = AKIDetGetCounterCyclebyId(busCallDetector, busVehiclePosition)  # Number of entering bus(es) in last step
    if enterNum > 0:
        cycled_bus = 0
        # enterNum_record = enterNum
        total_bus += 1

        print("------- No.{} Bus Checked -------".format(total_bus))
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
                f.write("%d " % total_bus)
                f.close()
                is_written = True
            except:
                print("failed writing files")
                continue

        for i in range(enterNum):
            # # Get action from outside

            # If first vehicle equals last vehicle of last step
            if i == 0 and busin_info.idVeh == last_in_info:
                # Skip first vehicle and loop
                continue
            else:
                numbus += 1
                allnumvel += 1

                # log info
                busintime_list.append(time)
                check_in_hdy_L.append(busintime_list[-1] - busintime_list[-2])
                check_in_phase_no_L.append(currentPhase)
                check_in_phaseTime_L.append(phasetime)

                extended = red_extend + green_extend
                if currentPhase == 1:
                    tToNearGreenPhase = 104 - phasetime + extended
                elif currentPhase == 2:
                    tToNearGreenPhase = 104 - phasetime + extended - 16
                elif currentPhase == 3:
                    tToNearGreenPhase = 104 - phasetime + extended - 54
                elif currentPhase == 4:
                    tToNearGreenPhase = 104 - phasetime + extended - 61
                elif currentPhase == 5:
                    tToNearGreenPhase = 104 - phasetime + extended - 72
                elif currentPhase == 6:
                    tToNearGreenPhase = 110 - phasetime + extended

                if numbus > 1:
                    tToNearGreenPhase_list.append(tToNearGreenPhase)
                    allnumvel_list.append(allnumvel)
                
                if numbus == 1:
                    tt_target = butoutime_list[-1] - busintime_list[-1]
                    
                    # Update states
                    updated = -updated
                    output = [tt_target, tToNearGreenPhase, allnumvel, butoutime_list[-2], butoutime_list[-1],
                              butoutime_list[-1] - busintime_list[-2], remain, busintime_list[-3], busintime_list[-2], updated]
                    print("Output: {}".format(output))
                    f = open(TransferToDQN, "w+")
                    for j in output:
                        f.write("%f " % j)
                    f.close()

                    # log states
                    states.append([tt_target, tToNearGreenPhase, allnumvel])

                    # Extend the phase for extended time
                    extend_green_phase(time, timeSta, currentPhase, phasetime, False)


        last_in_info = temp_info.idVeh


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
            if i == 0 and busout_info.idVeh == last_out_info:
                # Skip first vehicle and loop
                continue
            else:
                numbus -= 1
                allnumvel -= 1
                print("Bus banching %d" % numbus)

                butoutime_list.append(time)
        
                travelTime = butoutime_list[-1] - busintime_list[-2] if numbus >= 1 else butoutime_list[-1] - busintime_list[-1]


                ##### log #########
                log_parameter_file(busout_info, phasetime)
                ###### log #######

                print("red_extend: {}".format(red_extend))
                print("green_extend: {}".format(green_extend))
                print("Green phase remaining at exit: {}".format(remain))

                if numbus >= 1:
                    tt_target = butoutime_list[-1] - busintime_list[-1]

                    # Update states
                    updated = -updated
                    output = [tt_target, tToNearGreenPhase_list[0], allnumvel_list[0]-1, butoutime_list[-2], butoutime_list[-1],
                              butoutime_list[-1] - busintime_list[-2], remain, busintime_list[-3], busintime_list[-2], updated]
                    print("Output: {}".format(output))
                    f = open(TransferToDQN, "w+")
                    for j in output:
                        f.write("%f " % j)
                    f.close()

                    # log states
                    states.append([tt_target, tToNearGreenPhase_list[0], allnumvel_list[0]-1])

                    tToNearGreenPhase_list.pop(0)
                    allnumvel_list.pop(0)

                    # extend green phase
                    extend_green_phase(time, timeSta, currentPhase, phasetime, True)
                    

        last_out_info = temp_info.idVeh
    

    if len(butoutime_list) > 10 and len(busintime_list) > 10:
        butoutime_list = butoutime_list[6:]
        busintime_list = busintime_list[6:]

    return 0


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


