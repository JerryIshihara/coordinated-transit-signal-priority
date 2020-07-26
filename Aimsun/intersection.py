"""Summary
"""
from AAPI import *
from util import *
from BusInPoz import *
import csv

class Intersection:
    """Summary

    Attributes
    ----------
    allnumvel : int
        Description
    bunch_list : list
        Description
    busin_info : int
        Description
    busininfo_list : list
        Description
    busintime_list : list
        Description
    CONFIG : TYPE
        Description
    extend_record : dict
        Description
    extended : int
        Description
    extendedalready : int
        Description
    in_bus : list
        Description
    in_list : list
        Description
    last_in_info : int
        Description
    last_out_info : int
        Description
    LOG : TYPE
        Description
    markedbus : int
        Description
    markedbusgone : int
        Description
    numbus : int
        Description
    out_list : list
        Description
    POZactive : int
        Description
    tToNearGreenPhase_list : list
        Description
    """
    def __init__(self, CONFIG):
        """Summary

        Parameters
        ----------
        CONFIG : TYPE
            Description
        """
        self.CONFIG = CONFIG
        self.cycled_bus = 0
        self.total_bus = 0
        self.bunch_list = []
        self.in_bus = []
        self.in_list = [0]
        self.out_list = [0]
        self.tToNearGreenPhase_list = []
        self.extended = 0
        self.busintime_list = []
        self.busininfo_list = []
        self.numbus = 0
        self.allnumvel = 0
        self.last_in_info = -99
        self.last_out_info = -99
        self.extendedalready = 0  # extended or not in current cycle
        self.markedbus = 0  # if a bus is marked as indicator
        self.markedbusgone = 0  # if a marked bus had exited
        self.busin_info = 0
        self.replicationID = None
        self.extend_record = {}
        self.LOG = self.CONFIG['log']

    def get_state(self):
        """Return a list containing prePOZ state and POZ state (8 slots)

        based on 3 conditions: 
        1. bus in prePOZ 
        2. bus in POZ
        3. no bus
        
        Returns
        -------
        list
            a list containing prePOZ state and POZ state
        """
        # TODO: get the newest state information
        prePOZ = ...
        POZ = ...
        return [*prePOZ, *POZ]

    def apply_action(self, action):
        """Apply the action to the intersection according to different 
        situations (hard code for upstream)
        
        Parameters
        ----------
        action : int
            action to the intersection
        """
        # TODO: change intersection phase time using action
        None

    def get_reward(self):
        """Return the reward of the most current bus check-out event, and
        CLEAR the reward attribute
        
        Returns
        -------
        float
            the reward of the most current bus check-out event
        """
        reward, self.reward = self.reward, 0
        return reward

    def _compute_reward(self, travelTime, bus_object):
        """Compute reward gained by a newly checked out bus

        Parameters
        ----------
        travelTime : TYPE
            Description
        bus_object : TYPE
            Description
        """
        d_out = abs(bus_object.check_out_headway -
                    self.CONFIG['target_headway'])
        d_in = abs(bus_object.check_in_headway - self.CONFIG['target_headway'])
        improve = d_in - d_out
        self.reward = 0.6 * improve - 0.4 * travelTime
        
    def _get_toNearGreenPhase(self, currentPhase, phasetime, extended):
        """Calculate the time to the nearest focus phase green signal.

        Parameters
        ----------
        currentPhase : int
            current intersection phase
        phasetime : int
            passed time from start of the current phase
        extended : int
            applied cumulated action on the intersection

        Returns
        -------
        int
            the time to the nearest focus phase green signal
        """
        if currentPhase <= self.CONFIG['phase_of_interest']:
            to_interest = time_to_phase_end(self.CONFIG['phase_duration'],
                                            self.CONFIG['phase_of_interest'])
            past_phase = time_to_phase_end(self.CONFIG['phase_duration'],
                                           currentPhase - 1)
            return to_interest - phasetime + extended - past_phase
        return sum(self.CONFIG['phase_duration']) - phasetime + extended

    def _bus_enter_handler(self, time):
        """Summary

        Parameters
        ----------
        time : TYPE
            Description

        ------------------
        TYPE
            Description
        """
        # retrieve intersection info from CONFIG
        intersection = self.CONFIG['intersection']
        busCallDetector = self.CONFIG['busCallDetector']
        section = self.CONFIG['section']
        # get bus internal position
        busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)  
        target_headway = self.CONFIG['target_headway']
        self.replicationID = ANGConnGetReplicationId()
        # determine which phase is green in the bus's perspective
        phase_of_interest = self.CONFIG['phase_of_interest']
        # assumption for this is that all phases has duration defined
        total_phases = len(self.CONFIG['phase_duration'])
        # current phase time
        phasetime = time - ECIGetStartingTimePhase(intersection)
        # get current phase
        currentPhase = ECIGetCurrentPhase(intersection)
        # find phase before and after phase of interest
        phase_after_phase_of_interest = get_phase_number(
            total_phases, phase_of_interest + 1)
        phase_before_phase_of_interest = get_phase_number(
            total_phases, phase_of_interest - 1)
        # green phase ended and the buses that are still in POZ becomes cycled buses
        if currentPhase == phase_after_phase_of_interest and phasetime == 0:
            self.cycled_bus = self.numbus
        if currentPhase != phase_of_interest and (self.numbus - self.cycled_bus == 0):
            self.green_extend = 0
            ECIChangeTimingPhase(
                intersection, 
                phase_of_interest,
                self.CONFIG['phase_duration'][phase_of_interest - 1], 
                timeSta)
        # if currentPhase != 4 and (self.numbus - self.cycled_bus == 0):
        #     self.red_extend = 0
        #     ECIChangeTimingPhase(
        #         intersection, 
        #         phase_before_phase_of_interest,
        #         self.CONFIG['phase_duration'][phase_before_phase_of_interest -1],
        #         timeSta)
        # Check number of all vehicles in and out
        self.allnumvel = AKIVehStateGetNbVehiclesSection(section, True)
        # bus enter check
        enterNum = AKIDetGetCounterCyclebyId(
            busCallDetector,
            busVehiclePosition)  # Number of entering bus(es) in last step

        new_state = []
        new_bus_entered = False

        if enterNum > 0:
            self.cycled_bus = 0
            self.total_bus += 1
            print("------- No.{} Bus Checked -------".format(self.total_bus))
            # First vehicle info
            busin_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busCallDetector, 0, busVehiclePosition)
            # Last vehicle info
            temp_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busCallDetector,
                AKIDetGetNbVehsEquippedInDetectionCyclebyId(busCallDetector, busVehiclePosition) - 1,
                busVehiclePosition)

            # is_written = False
            # while not is_written:
            #     try:
            #         f = open(Num_bus_in_rep, "w+")
            #         f.write("%d " % self.total_bus)
            #         f.close()
            #         is_written = True
            #     except:
            #         print("failed writing files")
            #         continue

            for i in range(enterNum):
                # If first vehicle equals last vehicle of last step
                if i == 0 and busin_info.idVeh == self.last_in_info:
                    # Skip first vehicle and loop
                    continue
                else:
                    new_bus_entered = True
                    if self.list_of_bus_in_POZ:
                        last_check_in_time = self.list_of_bus_in_POZ[-1].check_in_time
                    else:
                        last_check_in_time = time - target_headway  # for the first bus, assume that the check in headway is perfect
                    self.list_of_bus_in_POZ.append(
                        BusInPoz(
                            intersection, 
                            busin_info,
                            currentPhase,
                            phasetime,
                            time,
                            last_check_in=last_check_in_time)
                        )
                    self.numbus += 1
                    self.allnumvel += 1
            self.last_in_info = temp_info.idVeh

            # TODO: return True when bus check-in

    def _bus_out_handler(self, time):
        """Summary

        Parameters
        ----------
        time : TYPE
            Description
        """
        # retrieve intersection info from CONFIG
        intersection = self.CONFIG['intersection']
        busExitDetector = self.CONFIG['busExitDetector']
        section = self.CONFIG['section']
        # get bus internal position
        busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)  
        target_headway = self.CONFIG['target_headway']
        self.replicationID = ANGConnGetReplicationId()
        # determine which phase is green in the bus's perspective
        phase_of_interest = self.CONFIG['phase_of_interest']
        # assumption for this is that all phases has duration defined
        total_phases = len(self.CONFIG['phase_duration'])
        # current phase time
        phasetime = time - ECIGetStartingTimePhase(intersection)
        # get current phase
        currentPhase = ECIGetCurrentPhase(intersection)
        # find phase before and after phase of interest
        phase_after_phase_of_interest = get_phase_number(
            total_phases, phase_of_interest + 1)
        phase_before_phase_of_interest = get_phase_number(
            total_phases, phase_of_interest - 1)
        # green phase ended and the buses that are still in POZ becomes cycled buses
        if currentPhase == phase_after_phase_of_interest and phasetime == 0:
            self.cycled_bus = self.numbus
        if currentPhase != phase_of_interest and (self.numbus - self.cycled_bus == 0):
            self.green_extend = 0
            ECIChangeTimingPhase(
                intersection, 
                phase_of_interest,
                self.CONFIG['phase_duration'][phase_of_interest - 1], 
                timeSta)
        # if currentPhase != 4 and (self.numbus - self.cycled_bus == 0):
        #     self.red_extend = 0
        #     ECIChangeTimingPhase(
        #         intersection, 
        #         phase_before_phase_of_interest,
        #         self.CONFIG['phase_duration'][phase_before_phase_of_interest -1],
        #         timeSta)
        # Check number of all vehicles in and out
        self.allnumvel = AKIVehStateGetNbVehiclesSection(section, True)
        # bus enter check
        enterNum = AKIDetGetCounterCyclebyId(
            busCallDetector,
            busVehiclePosition)  # Number of entering bus(es) in last step

        new_state = []
        new_bus_entered = False
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

                    reward_gained = _compute_reward(travelTime, checked_out_bus)
                    self.cumulative_reward += reward_gained
                    print("Reward gained at checked out: {}".format(reward_gained))

            self.last_out_info = temp_info.idVeh

        extended = self.red_extend + self.green_extend
        tToNearGreenPhase = self._get_toNearGreenPhase(currentPhase, phasetime, 0)
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

        # TODO: return True when bus check-out



