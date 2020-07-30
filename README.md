# Coordinated Transit Signal Priority (cTSP)
<img src='https://img.shields.io/badge/project-in progress-yellow'>
## Introduction
<img src="/demo/tsp_flow.png" width="700"/> <br />
Coordinate Transit Signal Priority with two traffic intersections in Toronto area, improving speed and reliability with a single deep reinforcement learning agent.
## Usage
### 1. Clone the repository
### 2. Load Python script to Aimsun model
  - open Aimsun Next 8.3 and load the target Aimsun model
  - double click the dynamic senerio in the project list on the right of the screen
  - select the `Aimsun Next APIs` tab in the pop-up window
    <img src="/demo/navBar.png" width="700"/> <br />
  - click `add` and load the file `detector.py` from the cloned repository (and inacvtive all other scripts)
  - save the model and close Aimsun Next
### 3. Open the jupyter notebook ```agent.ipynb```, and run the first cell.
### 4. Start the training by **either**
a. running `train.sh` in terminal:

```
sh ./train.sh -p PYTHON_DIR -a ACONSOLE_PATH -m MODEL_PATH -s START_REP -e END_REP
```
b. copying the following to termial:
```
cd PYTHON_DIR

for /l %x in (START_REP, 1, END_REP) do (python "CONTROLLER_PATH" -aconsolePath "ACONSOLE_PATH" -modelPath "MODEL_PATH" -targets %x)
```
where 
- `PYTHON_DIR`: Python 2 directory 
- `ACONSOLE_PATH`: path to Aimsun 8.3 exacutable file 
- `CONTROLLER_PATH`: path to `RunSeveralReplications.py`
- `MODEL_PATH`: path to Aimsun model
- `START_REP`, `END_REP`: start and end replication numbers 

## Model Set-up
### 1.	Time step
Time steps are renewed upon bus check-in events (should avoid bug if more than one bus checked in at the same time. For example, Bus A checks in at time x at Intx 1, and Bus B checks in at time x at Intx 2.). 
A time step is a time point at which a bus is detected by a loop detector. Every check-in event at any check-in loop detector in the system (a system includes all intersections and road segments connecting these intersections) would initiate a new time step. 
> Example: Bus 1, 2 and 3 are in the system at time step t. When Bus 4 checks in, time step t+1 is initiated.

At each time step, the RL model 
- reads the state of the current environment, 
- chooses an action, and 
- calculates the reward of the last time step.

### 2.	State
States are collected when time steps are renewed. A state includes observations at all intersections in the system which contains bus-, traffic-, and signal-related information. Each intersection has following observations:
<img src="/demo/prePOZ.png" width="700"/> <br />
- Upstream of the POZ, downstream of the upstream intersection (prePOZ)
  - Check-out time of the bus closest to the downstream POZ
  - number of buses
- In the POZ
  - Last available check-out time
  > If bunch (POZ has more than one bus, Number of buses > 1): use the current time as the check-out time
  - Check-in time of the current bus (current time) that initiated this time step
  - Check-in headway
  - Number of buses in the POZ, 
  - Number of cars in the POZ
  - Time to the end of EW green: exclude any registered action 
  > Registered action: any action that has not been executed but planned, or is now being executed at the time of check-in
### 3.	Action
Action is chosen at every time step as soon as the state is received by the RL model. Actions make adjustment of the durations of the first available EW green for each intersection at time step t. 
- If a bus checked in during EW red, adjustment is made to the first available EW green following the red
- If a bus checked in during EW green, adjustment is made to the current EW green
> Example:
  A bus checks in at intersection 1 at time step t. At time step t, the phase at Intx 1 is red in the direction of bus movement, the adjustment is made to the EW     green following red. At time step t, the phase at Intx 2 is EW green, the adjustment is made to this EW green.
  
To ensure consistency with iTSP, actions are EW green truncations of -20, -15, -10, -5, do-nothing, green extensions of +5, +10, +15, +20s.
  
<img src="https://bit.ly/32UbYn9" align="center" border="0" alt="a_t = (a_t^1, a_t^2)" width="133" height="31" />

When at is selected, if there is a registered action (maybe decided at time step t-1) for an intersection, at would overwrite at-1 if possible.
If a truncation action is selected, and the truncation amount > remaining EW green, EW green would be end “now.”
### 4.	Reward
Reward associated with state and action at time step t is calculated at time step t+1. Rewards are computed using data (headway and travel time in the POZ) of all check-out events occurred between time step t and t+1.
> Example: 
If bus A and B checked out two different intersections (or the same intersection) between time step t and t+1, rt = rA + rB =  0.6*(headway improvement of bus A) – 0.4*(travel time of bus A in the POZ) + 0.6*(headway improvement of bus B) – 0.4*(travel time of bus B in the POZ)

If no bus checked out between time step t and t+1, rt = 0.


