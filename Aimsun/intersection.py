from AAPI import *
import csv

# =============== util =====================


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


# =============== util =====================


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
        self.POZactive = 0
        self.extend_record = {}
        self.LOG = self.CONFIG['log']

    def get_toNearGreenPhase(self, currentPhase, phasetime, extended):
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
            t = to_interest - phasetime + extended - past_phase
        else:
            t = sum(self.CONFIG['phase_duration']) - phasetime + extended
        print('currentPhase: {}   phaseTime: {}   extended: {}'.format(
            currentPhase, phasetime, extended))
        print(self.CONFIG['phase_duration'])
        print('to nearest green: {}'.format(t))
        return t

    def _bus_enter_handler(self, time):
        """Summary

        Returns
        -------
        TYPE
            Description
        """
        intersection = self.CONFIG['intersection']
        busCallDetector = self.CONFIG['busCallDetector']
        # get bus internal position
        busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)
        # current phase time
        phasetime = time - ECIGetStartingTimePhase(intersection)
        # get current phase
        currentPhase = ECIGetCurrentPhase(intersection)
        # number of buses entered
        enterNum = AKIDetGetCounterCyclebyId(busCallDetector,
                                             busVehiclePosition)
        if enterNum > 0:
            print("{}: Bus enter {}".format(intersection, enterNum))
            # First vehicle info
            self.busin_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(busCallDetector, 0, busVehiclePosition)
            # Last vehicle info
            temp_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busCallDetector, enterNum - 1, busVehiclePosition)
            for i in range(enterNum):
                # If first vehicle equals last vehicle of last step
                if i == 0 and self.busin_info.idVeh == self.last_in_info:
                    # Skip first vehicle and loop
                    continue
                else:
                    self.numbus += 1
                    print("Bus after entered %d" % self.numbus)
                    self.busintime_list.append(time)
                    self.busininfo_list.append(
                        AKIDetGetInfVehInDetectionInfVehCyclebyId(
                            busCallDetector, i, busVehiclePosition).idVeh)
                    self.tToNearGreenPhase_list.append(
                        self.get_toNearGreenPhase(currentPhase, phasetime,
                                                  self.extended))
                    self.in_list.append(time)
                    self.in_bus.append(self.busin_info.idVeh)
                    self.bunch_list.append(self.numbus > 1)
                    self.extend_record[self.busin_info.idVeh] = 0
            self.last_in_info = temp_info.idVeh

    def _bus_out_handler(self, time):
        intersection = self.CONFIG['intersection']
        busExitDetector = self.CONFIG['busExitDetector']
        # get bus internal position
        busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)
        # current phase time
        phasetime = time - ECIGetStartingTimePhase(intersection)
        currentPhase = ECIGetCurrentPhase(intersection)  # get current phase
        # Number of exit vehicle in last step
        exitNum = AKIDetGetCounterCyclebyId(busExitDetector,
                                            busVehiclePosition)
        if exitNum > 0:
            # First vehicle info
            busout_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busExitDetector, 0, busVehiclePosition)
            # Last vehicle info
            temp_info = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                busExitDetector, exitNum - 1, busVehiclePosition)
            for i in range(exitNum):
                # If first vehicle equals last vehicle of last step
                if i == 0 and busout_info.idVeh == self.last_out_info:
                    # Skip first vehicle and loop
                    continue
                else:
                    self.numbus -= 1
                    if self.numbus == -1:
                        self.numbus = 0
                    print("Bus after exited %d" % self.numbus)

                    self.out_list.append(time)
                    travelTime = time - self.busintime_list[0]
                    in_dev = self.in_list[1] - self.in_list[0] - 290
                    out_dev = self.out_list[-1] - self.out_list[-2] - 290
                    # check if the marked bus has exited
                    temp_out = AKIDetGetInfVehInDetectionInfVehCyclebyId(
                        busExitDetector, i, busVehiclePosition)
                    one_cycle = 1 if travelTime <= self.tToNearGreenPhase_list[0] + \
                        self.extend_record[temp_out.idVeh] + 3 else 0
                    print("[{}]: {} Bus extended {}".format(
                        intersection, temp_out.idVeh,
                        self.extend_record[temp_out.idVeh]))
                    if temp_out.idVeh == self.markedbus:
                        self.markedbusgone = 1
                        self.markedbus = 0
                    log = [
                        ANGConnGetReplicationId(), self.allnumvel,
                        self.busintime_list[0], time,
                        self.extend_record[temp_out.idVeh], 'EB', travelTime,
                        in_dev, out_dev, self.bunch_list[0], one_cycle,
                        self.tToNearGreenPhase_list[0], self.in_bus[0],
                        busout_info.idVeh
                    ]
                    # else:
                    #     log = [
                    #         ANGConnGetReplicationId(), self.allnumvel, self.busintime_list[0],
                    #         time,self.extend_record[busout_info.idVeh], 'EB',
                    #         travelTime, in_dev, out_dev, self.bunch_list[0],
                    #         one_cycle, self.tToNearGreenPhase_list[0],
                    #         self.in_bus[0], busout_info.idVeh
                    #     ]
                    # Log extension for each exiting bus
                    print(log)
                    with open(self.LOG, "a+") as out:  # Log key parameters
                        csv_write = csv.writer(out, dialect='excel')
                        csv_write.writerow(log)
                    # Removing the 1st vehicle enter info
                    self.busintime_list.pop(0)
                    self.busininfo_list.pop(0)
                    self.tToNearGreenPhase_list.pop(0)
                    self.in_list.pop(0)
                    self.out_list.pop(0)
                    self.in_bus.pop(0)
                    self.bunch_list.pop(0)

            self.last_out_info = temp_info.idVeh

    def POZ_handler(self, time, timeSta, timeTrans, acycle):
        """Summary

        Parameters
        ----------
        time : TYPE
            Description
        timeSta : TYPE
            Description
        timeTrans : TYPE
            Description
        acycle : TYPE
            Description

        Returns
        -------
        TYPE
            Description
        """
        intersection = self.CONFIG['intersection']
        section = self.CONFIG['section']
        # current phase time
        phasetime = time - ECIGetStartingTimePhase(intersection)
        currentPhase = ECIGetCurrentPhase(intersection)  # get current phase
        if currentPhase == self.CONFIG[
                'phase_of_interest'] + 1 and phasetime == 1:
            self.extended = 0
        # Check number of all vehicles in and out
        self.allnumvel = AKIVehStateGetNbVehiclesSection(section, True)

        self._bus_enter_handler(time)
        self._bus_out_handler(time)

        # check if POZ is active at decision point (end of WALK)
        decision = self.CONFIG['AlgB_decision']
        phase_interest = self.CONFIG['phase_of_interest']
        phase_end = self.CONFIG['phase_duration'][phase_interest - 1]

        if self.numbus > 0 and decision - 1 < phasetime < decision + 1 and currentPhase == phase_interest:
            print("POZ active at decision point")
            self.POZactive = 1

        # check bus presence over busCallDetector and extend the phase for extended time
        if self.numbus > 0 and self.POZactive == 1 and phasetime >= phase_end and currentPhase == phase_interest and self.extendedalready == 0:
            if self.extended <= 14 and self.markedbusgone == 0:  # Phase 5: EB through
                if self.markedbus == 0:
                    self.markedbus = self.busininfo_list[0]
                ECIChangeDirectPhase(intersection, currentPhase, timeSta, time,
                                     acycle, phasetime - 2)
                self.extended += 2
                print("[{}] {} eligible for extension {}".format(
                    intersection, self.markedbus, self.extended))
                self.extend_record[self.markedbus] = self.extended
            else:
                self.extendedalready = 1

        if currentPhase != phase_interest:
            self.markedbusgone = 0
            self.extendedalready = 0
            self.POZactive = 0

        return 0



