cd/d C:\Python27

for /l %x in (1176291, 1, 1177590) do (python "D:\AimSun Python\Aimsun Controller\RunSeveralReplications.py" -aconsolePath "C:\Program Files\Aimsun\Aimsun Next 8.3\aconsole.exe" -modelPath "D:\AimSun Python\GTAModel_finchTSPs_8.3.ang" -targets %x)