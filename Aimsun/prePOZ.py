class PrePoz:
    
    def __init__(self, config):
    	self.CONFIG = config
    	self.last_in_info = None
    	self.last_out_info = None
    	self.time_list = []

    def get_state(self):
    	if len(self.time_list) == 0:
    		return [0, 0]
    	return [self.time_list[0], len(self.time_list)]

    def update(self, time, timeSta):
    	self._enter_prePOZ(time, timeSta)
    	self._exit_prePOZ(time, timeSta)        

    def _enter_prePOZ(self, time, timeSta):
    	# retrieve intersection info from CONFIG
        busExitDetector = self.CONFIG['busExitDetector']
        # get bus internal position
        busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)  
        # bus exit check
        exitNum = AKIDetGetCounterCyclebyId(busExitDetector, busVehiclePosition)  # Number of exit vehicle in last step
        if exitNum > 0:
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
                	print("prePOZ-{} enter-{}".format(busExitDetector, time))
                	self.time_list.append(time)
            self.last_out_info = temp_info.idVeh


    def _exit_prePOZ(self, time, timeSta):
        busCallDetector = self.CONFIG['busCallDetector']
        # get bus internal position
        busVehiclePosition = AKIVehGetVehTypeInternalPosition(1171922)  
        # bus enter check 
        enterNum = AKIDetGetCounterCyclebyId(busCallDetector, busVehiclePosition)  
        if enterNum > 0:
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
                	print("prePOZ-{} exit-{}".format(busCallDetector, time))
                	self.time_list.pop(0)

            self.last_in_info = temp_info.idVeh


