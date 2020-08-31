# -*- coding: utf-8 -*-
"""Summary
"""
from AAPI import *
from BusInPOZ import BusInPOZ
from util import *
import util
import csv

class Intersection:

    """Summary

    Attributes
    ----------
    CONFIG : dict
        configuration of the intersection, see config.py
    cycled_bus : int
        bus that checked in at the previous cycle (a cycle start at phase of interest and end before the next phase of interest)
    total_bus : int
        total number of bus enetered this intersection (used to determine the first & last checked in bus in training)
    bus_list : list
        list of bus object CURRENTLY in the intersection （has not checked out yet)
        arranged by check in time, with the newest bus at the end of the list
    last_checkout_bus : BusInPOZ object
        the latest bus that checked out of the intersection, initialized as None before the first bus checkout event
    extended : int
        Registered action that is applied on this intersection
    extendedalready : int
        0 or 1, 0 means no change has been made to the intersection signal length
    numbus : int
        Number of bus CURRENTLY in the intersection POZ
    allnumvel : int
        Number of bus + cars currently in the intersection POZ
    last_in_info : int
        The bus id of the bus which initiated the last check in event (used to avoid repeated check in event)
    last_out_info : int
        The bus id of the bus which initiated the last check out event (used to avoid repeated check out event)
    markedbus : int
        not used yet
    markedbusgone : int
        not used yet
    reward : int
        cumulative reward collected in check out events after the last check in event
    replicationID : int
        Aimsun replication ID for the current simulation
    downstream_intersection : Intersection object
        pointer to the downstream intersection
    prePOZ_numbus : int
        (initialized to None to indicate no upstream intersection exist to the current intersection)
        number of bus in prePOZ of the current intersection, this number should only be increased by the intersection before
        this intersection
    prePOZ_bus_checkout_time_dict : dict
        dict with bus id as keys and bus checkout time as values. This shows all bus in prePOZ of the current intersection
        This dict is only valid IF there is a detector/intersection before the current intersection
    state ： list with 6 elements
        infomation about the bus and vehicles INSIDE POZ (not including prePOZ)
        [last_available_checkout_time, last_check_in_time, check_in_headway,
        number of buses in POZ, number of cars + buses in POZ, time To Nearest Green]

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
        self.bus_list = [] # list of bus in POZ
        self.last_checkout_bus = None
        self.extended = 0 # registered action
        self.numbus = 0
        self.allnumvel = 0
        self.last_in_info = -99 # bus id for last checked in bus
        self.last_out_info = -99
        self.extendedalready = 0  # extended or not in current cycle
        # self.markedbus = 0  # if a bus is marked as indicator
        # self.markedbusgone = 0  # if a marked bus had exited
        self.reward = 0  # cumulative reward
        self.replicationID = None
        # self.extend_record = {}
        self.downstream_intersection = None

        # number of bus in prePOZ will produce error if a bus enters POZ without being recorded in prePOZ (aka checkout from last intersection)
        self.prePOZ_numbus = None
        self.prePOZ_bus_checkout_time_dict = None  # this dict is only valid if there is a detector/intersection before this intersection

        self.state = [0, 0, 0, 0, 0, 0]

    # def set_downstream_intersection(self, intersection):
    #     """
    #     set the intersection after the current intersection
    #     (so checked out buses are written to next intersection's prePOZ)

    #     Parameters
    #     ----------
    #     intersection : Intersection
    #         Intersection object for the intersection immediately after the current intersection

    #     """
    #     self.downstream_intersection = intersection
    #     # initialize the prePOZ for next intersection
    #     # dict key is bus id
    #     self.downstream_intersection.prePOZ_bus_checkout_time_dict = {}
    #     self.downstream_intersection.prePOZ_numbus = 0
    #     return

    def _find_first_checkout_time_in_prePOZ(self):
        """
        find the last

        Returns
        -------
        first_checkout_time : int
            the checkout time of the first bus in prePOZ
        """
        if self.prePOZ_numbus is None or self.prePOZ_numbus == 0:
            return 0
        prePOZ_busdict = self.prePOZ_bus_checkout_time_dict
        first_checkout_time = min(prePOZ_busdict, key=prePOZ_busdict.get)
        return first_checkout_time

    def _checkout_bus_from_POZ(self, checkout_id, checkout_time):
        # remove bus with corresponding id from POZ and return the bus
        for bus in self.bus_list:
            if bus.bus_id == checkout_id:
                if self.last_checkout_bus is not None:
                    last_checkout_time = self.last_checkout_bus.check_out_time
                else:
                    # if there is no previous bus, assume checkout headway is perfect
                    last_checkout_time = checkout_time - self.CONFIG['target_headway']
                bus.check_out(checkout_time, last_checkout_time)
                self.bus_list.remove(bus)
                if self.downstream_intersection is not None:
                    # record the checkout bus and checkout time for the prePOZ of the next intersection
                    self.downstream_intersection.prePOZ_bus_checkout_time_dict[checkout_id] = checkout_time
                return bus
        return False

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

        if self.prePOZ_numbus is None:
            prePOZ = [0, 0]
        else:
            prePOZ = [len(self.prePOZ_bus_checkout_time_dict.keys()), self._find_first_checkout_time_in_prePOZ()]

        return self.state

    def set_bus_actions_and_state(self, actions, joint_state):
        """
        save the action decided by DQN at bus checkin onto the bus object so it can be compared with the actual action applied
        Parameters
        ----------
        actions : list of int
            action to all intersections
        joint_state : list of int
            joint state of the intersections
        """
        self.bus_list[-1].set_action(actions)
        self.bus_list[-1].set_state(joint_state)
        return

    def apply_action(self, action, time, timeSta):
        """Apply the action to the intersection according to different 
        situations (hard code for upstream)
        
        Parameters
        ----------
        action : int
            action to the intersection (extend/shorten this amount)
        time : int
            Absolute time of simulation in seconds
        timeSta : int
            Time of simulation in stationary period, in sec
        """

        if self.numbus == 0 and self.prePOZ_numbus is None:
            # this means this is the upstream intersection AND there is no bus here
            # ^^^ this is hardcoded for now, in the future each intersection should has a pointer to its previous
            #       intersection and check that if there is no bus in all upstream intersections and current
            #       intersection, force the action to be zero
            action = 0
        intersection = self.CONFIG['intersection']
        phase_of_interest = self.CONFIG['phase_of_interest']
        total_phases = len(self.CONFIG['phase_duration'])
        green_duration = self.CONFIG['phase_duration'][phase_of_interest - 1]

        # TODO: changing the intersection time might not be legal! need to handle this
        ECIChangeTimingPhase(intersection, phase_of_interest, green_duration + action, timeSta)
        if action != 0:
            self.extendedalready = 1
        self.extended = action

        print("------- {} Extend start here ----------".format(intersection))
        print("Extended at time: {}".format(time))
        print("Extended length: " + str(action) + " sec")

    def log_parameter_file(self, phasetime, checked_out_bus):
        replicationID = ANGConnGetReplicationId()
        vehicleID = checked_out_bus.bus_id
        target_headway = self.CONFIG['target_headway']
        parameter_log_file = self.CONFIG['log']
        reward = self.reward
        check_out_hdy = checked_out_bus.check_out_headway
        travelTime = checked_out_bus.check_out_time - checked_out_bus.check_in_time
        state = checked_out_bus.original_state
        if state is None:
            state = [-99]*16
        action = checked_out_bus.original_action
        if action is None:
            action = [-99]*2

        # list of things in log by index
        # 0: replication ID
        # 1: vehicle ID
        # 2: checkout time
        # 3: check in phase number
        # 4: check in phase time
        # 5: checkout phase time
        # 6: checkout headway
        # 7 - 8: action 1, action 2 as decided at the bus check in
        # 9: registered action at bus check out
        # 10: Travel time
        # 11+: states

        # the same cycle
        output = [replicationID, vehicleID, checked_out_bus.check_out_time, checked_out_bus.check_in_phase,
                  checked_out_bus.check_in_phasetime, phasetime, check_out_hdy] + list(action) + [self.extended, travelTime] + state

        with open(parameter_log_file, "a+") as out:  # Log key parameters
            csv_write = csv.writer(out, dialect='excel')
            csv_write.writerow(output)
        return

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
        reward = 0.6 * improve - 0.4 * travelTime
        return reward
        
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
            to_interest = util.time_to_phase_end(self.CONFIG['phase_duration'],
                                            self.CONFIG['phase_of_interest'])
            past_phase = util.time_to_phase_end(self.CONFIG['phase_duration'],
                                           currentPhase - 1)
            return to_interest - phasetime + extended - past_phase
        return sum(self.CONFIG['phase_duration']) - phasetime + extended

    def _bus_enter_handler(self, time, timeSta):
        """Summary

        Parameters
        ----------
        time : int
            Absolute time of simulation in seconds
        timeSta : int
            Time of simulation in stationary period, in sec

        Returns
        -------
        bool
            True if a bus has entered this intersection
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
        phase_after_phase_of_interest = util.get_phase_number(total_phases, phase_of_interest + 1)
        # green phase ended and the buses that are still in POZ becomes cycled buses
        if currentPhase == phase_after_phase_of_interest and phasetime == 0:
            self.cycled_bus = self.numbus
            self.extendedalready = 0 # clear the extended already flag
        if currentPhase != phase_of_interest and (self.numbus - self.cycled_bus == 0):
            self.green_extend = 0
            ECIChangeTimingPhase(
                intersection, 
                phase_of_interest,
                self.CONFIG['phase_duration'][phase_of_interest - 1], 
                timeSta)

        # Check number of all vehicles in and out
        self.allnumvel = AKIVehStateGetNbVehiclesSection(section, True)
        # bus enter check
        enterNum = AKIDetGetCounterCyclebyId(
            busCallDetector,
            busVehiclePosition)  # Number of entering bus(es) in last step

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

            for i in range(enterNum):
                # If first vehicle equals last vehicle of last step
                if i == 0 and busin_info.idVeh == self.last_in_info:
                    # Skip first vehicle and loop
                    continue
                else:
                    new_bus_entered = True
                    if self.bus_list:
                        last_check_in_time = self.bus_list[-1].check_in_time
                    elif self.last_checkout_bus is not None:
                        # for the first bus, assume that the check in headway is perfect
                        last_check_in_time = self.last_checkout_bus.check_in_time
                    else:
                        last_check_in_time = time - target_headway
                    self.bus_list.append(BusInPOZ(intersection,
                                                    busin_info,
                                                    currentPhase,
                                                    phasetime,
                                                    time,
                                                    last_check_in=last_check_in_time)
                                         )
                    self.numbus += 1
                    self.allnumvel += 1
                    # if self.prePOZ_bus_checkout_time_dict is not None:
                    #     # this means there is data for prePOZ for this intersection
                    #     if self.prePOZ_numbus > 0:
                    #         self.prePOZ_numbus -= 1
                    #         try:
                    #             del self.prePOZ_bus_checkout_time_dict[busin_info.idVeh]
                    #         except KeyError:
                    #             raise KeyError("cannot find bus {} in prePOZ list, check if upstream intersection is "
                    #                   "recording bus checkout event correctly".format(busin_info.idVeh))
                    #     else:
                    #         print("prePOZ has no bus when a check in event happened, check if upstream intersection "
                    #               "is set correctly")

            self.last_in_info = temp_info.idVeh

        # update state
        self._update_state(currentPhase, phasetime, time)

        return new_bus_entered

    def _update_state(self, currentPhase, phasetime, time):
        """
        Update the state attribute of the intersection

        Parameters
        ----------
        currentPhase: int
            current traffic phase
        phasetime: int
            time (in sec) elapsed in the current traffic phase
        time: int
            Absolute time of simulation in seconds

        Returns
        -------
        None

        """
        # compute new state without registered action
        tToNearGreenPhase = self._get_toNearGreenPhase(currentPhase, phasetime, 0)
        if tToNearGreenPhase < 0:
            # already in an extended green phase
            tToNearGreenPhase = 0  # the green can end immediately

        if self.numbus > 0:
            # last available checkout for this intersection
            if self.numbus > 1:
                # bunch, use current time as last checkout
                last_available_checkout_time = time
            elif self.last_checkout_bus is None:
                # no checked out bus, assume perfect headway
                last_available_checkout_time = time - self.CONFIG['target_headway']
            else:
                last_available_checkout_time = self.last_checkout_bus.check_out_time
            # check in time of the last bus checked in
            last_check_in_time = self.bus_list[-1].check_in_time
            check_in_hdy = self.bus_list[-1].check_in_headway
            new_state = [last_available_checkout_time, last_check_in_time, check_in_hdy, self.numbus, self.allnumvel,
                         tToNearGreenPhase]
        else:
            new_state = [0, 0, 0, 0, 0, 0]

        self.state = new_state
        return

    def _bus_out_handler(self, time, timeSta):
        """Summary

        Parameters
        ----------
        time : int
            Absolute time of simulation in seconds
        timeSta : int
            Time of simulation in stationary period, in sec
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

        # Check number of all vehicles in and out
        self.allnumvel = AKIVehStateGetNbVehiclesSection(section, True)

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
                    if self.downstream_intersection is not None:
                        self.downstream_intersection.prePOZ_numbus += 1
                    print("Bus banching %d" % self.numbus)
                    checkout_id = busout_info.idVeh
                    successfully_checked_out_bus = self._checkout_bus_from_POZ(checkout_id, time)

                    if successfully_checked_out_bus is False:
                        raise Exception("Checkout detected for bus {}, but cannot found this bus in POZ".format(checkout_id))

                    self.last_checkout_bus = successfully_checked_out_bus
                    travelTime = successfully_checked_out_bus.check_out_time - successfully_checked_out_bus.check_in_time
                    # log parameters
                    self.log_parameter_file(phasetime, successfully_checked_out_bus)
                    reward_gained = self._compute_reward(travelTime, successfully_checked_out_bus)
                    self.reward += reward_gained
                    print("Reward gained at checked out: {}".format(reward_gained))

            self.last_out_info = temp_info.idVeh

        self._update_state(currentPhase, phasetime, time)

        return


