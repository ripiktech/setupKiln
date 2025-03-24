:START
cd /d "C:\Users\Ultratech-E&I\Desktop\kafka"
call python kiln_scheduler_rtsp_kafka.py
echo Script exited with error code %ERRORLEVEL%. Restarting in 5 seconds...
timeout /t 5 /nobreak > NUL
goto START