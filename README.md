# Coordinate Transit Signal Priority (cTSP)
## Introduction
<img src="/demo/tsp_flow.png" width="700"/> <br />
Coordinate Transit Signal Priority with two traffic intersections in Toronto area, improving speed and reliability with a single deep reinforcement learning agent.
## Usage
### 1. Clone the repository
```
git clone https://github.com/JerryIshihara/TSP-Research.git
```
### 2. Load Python script to Aimsun model
  - open Aimsun Next 8.3 and load the target Aimsun model
  - double click the dynamic senerio in the project list on the right of the screen
  <img src="/demo/dynamic_senario.png" width="500"/> <br />
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
- `PYTHON_DIR`: Python 2 directory <br />
server default: `C:\Python27`
- `ACONSOLE_PATH`: path to Aimsun 8.3 exacutable file <br />
server default: `C:\Program Files\Aimsun\Aimsun Next 8.3\aconsole.exe`
- `CONTROLLER_PATH`: path to `RunSeveralReplications.py` <br />
server default: `C:\Users\Public\Documents\ShalabyGroup\Aimsun Controller\RunSeveralReplications.py`
- `MODEL_PATH`: path to Aimsun model <br />
server default: `C:\Users\Public\Documents\ShalabyGroup\MODEL_NAME.ang`
- `START_REP`, `END_REP`: start and end replication numbers <br />
server default: 177671 to 1180580
