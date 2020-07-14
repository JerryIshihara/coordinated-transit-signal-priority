#!/bin/bash

# default server python directory
py_dir="C:\Python27"
# aimsun controller path
controller="~/Aimsun/RunSeveralReplications.py"
# default model path in the server
model_path="C:\Users\Public\Documents\ShalabyGroup\finchTSPs_3 intx_west_Subnetwork 1171379_newInters.ang"
# default aconsole path
aconsole_path="C:\Program Files\Aimsun\Aimsun Next 8.3\aconsole.exe"
# replicaion start and end
start=1177671 end=1180580

while [ "$1" != "" ]; do
    case $1 in
    	-p | --pythonDir )      shift
                                py_dir="$1"
                                ;;
        -m | --modelPath )      shift
                                model_path="$1"
                                ;;
        -a | --aconsolePath )   shift
								aconsole_path="$1"
                                ;;
		-s | --start )  		shift
								start=$1
                                ;;
		-e | --end )		    shift
								end=$1
                                ;;
    esac
    shift
done

echo ${end}

cd ${py_dir}

for /l %x in (${start}, 1, ${end}) do (python ${controller} -aconsolePath ${aconsole_path} -modelPath ${model_path} -targets %x)