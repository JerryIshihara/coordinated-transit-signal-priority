'''
Script to run several replications via Aconsole, one replication gets to run after the previous one finishes.

Usage of the script:
In command prompt go to where your Python 2.7 is located and type: python **PathToThisScript** -aconsolePath **PATHTO_aconsole.exe** -modelPath **PATHTOMODEL** -targets **Target1** **Target2** **...TargetN***
Where Target1, Target2 ... TargetN are replications or macroexperiments... 

You can also run several replications from several models by doing 

python **PathToThisScript** -aconsolePath **PATHTO_aconsole.exe** -modelPath **PATHTOMODEL1** -targets **Target1** **Target2** **...TargetN*** -modelPath  **PATHTOMODEL2** -targets **Target1** **Target2** ... 

'''



import sys
import os.path
import locale
from datetime import datetime
import subprocess # This library allows you to open a command prompt with aconsole.exe 

def RunSimulation(replicationID,modelPath): # This calls a subprocess like C:>ProgramFiles>Aimsuns>Aimsun Next 8.2_R5233>aconsole.exe -v -log -project **PROJECT** -cmd execute -target 1060
											#So each of the subprocesses generated by this function is an aconsole execution
	print "modelPath: " + modelPath
	print "replication id: " + str(replicationID)
	args = [execmd, '-v', '-log', '-project', modelPath, '-cmd', 'execute', '-target', replicationID]
	for x in range(0, 1):
		print(x)
		popen = subprocess.Popen(args)
		popen.wait() # This makes the script wait until the subprocess (aconsole) has finished. This way the memory consumption wont skyrocket. (There will be only one replication running at a time. )

argv=sys.argv # The arguments this script will take are the ones provided via command prompt

if argv[1] == '-aconsolePath':

	execmd = argv[2]
	print "\n Aconsole: " + execmd + "\n"

	if argv[3] == '-modelPath':
		modelPath = argv[4]
		print "------------\n"
		print "Model: " + modelPath + "\n"

	else:
		print "no -modelPath parameter"
		raw_input("Press enter to exit ;)")
		sys.exit()
else:
	print "No -aconsolePath parameter"
	raw_input("Press enter to exit ;)")
	sys.exit()

if argv[5] == '-targets':
	print "targets: \n "
	for i in range(len(argv[6:])):
		j = i +6
		if argv[j].isdigit():
			print argv[j] + "\n "
		else:
			if argv[j] =='-modelPath':
				print "------------\n"
				print "Model: " + argv[j+1] + "\n"

			if argv[j] == '-targets':
				print "targets: \n"
        print '===== NOW ===== \n'
        print datetime.now() 
else:
	print "no -targets parameter"
	raw_input("Press enter to exit ;)")
	sys.exit()


# answer = raw_input("Continue? [y/n] \n")
answer = 'y'
if answer == 'y':
	for j in range(len(argv[6:])):
		i = j+6
		if argv[i].isdigit():
			print "Running simulation: " + argv[i] + " in model: " + modelPath
			RunSimulation(argv[i],modelPath)
		elif argv[i] == '-modelPath':
			modelPath = argv[i+1]

else:
	print "execution canceled "
	raw_input("Press enter to exit ;)")
	sys.exit()
print "Done"
# raw_input("Press enter to exit ;)")

