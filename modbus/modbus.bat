:START
cd /d "C:\Users\utcl-gcw.processccr\Desktop\modbus"
call python modbusEpicIndex.py
echo Script exited with error code %ERRORLEVEL%. Restarting in 5 seconds...
timeout /t 5 /nobreak > NUL
goto START