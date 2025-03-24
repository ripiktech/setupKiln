# setupKiln

- This repo should be used for any new camera line setup for Ultratech Kiln (mainly for OnPrem)
- Enter the Kafka and AWS configuration values in the constants.py for it to work 

Steps to do for new kiln line addition (Onprem Configs)
    - Upload and extract the setupKiln folder
    - Download VS Code and open the given folder in it
    - Download python 3.10 and given requirements from SetupKiln folder
    - Download chocolatey
        - Go to chocolatey installation website copy the command and run it in powershell as an administrator
    - Download nssm
        - After chocolatey install nssm via: choco install nssm
    - Setup the service named kafkausing the given BAT file
        - run -> nssm install kafka
        - Select the bat file under kafka folder in setupKiln for image collection
    - In the bat file ensure that we are using the entire python path
        - To get the entire python path open a cmd and type python -> import sys -> sys.path -> copy the correct python path
    - Specify rtsp url and image upload path on s3 for the plant camera key (maihar1 -> rpk-clnt-in-prd/rpkultratech/kilnhealth/<camera_key>/) on MongoDB
    - Test the BAT file by double clicking it and check logs if a kafka event is being produced or not
    - Test the Windows service again by checking the logs and edit the Windows service properties to Restart The Service of any fail
AFTER KAFKA EVENTS ARE SUCCESSFULLY PRODUCED (Cloud Configs)
    - Specify model path for the plant camera key (maihar1 -> rpk-clnt-in-prd/rpkultratech/kilnhealth/models/<camera_key>/resnet18.pth) on MongoDB collection
    - Restart the consumers
        - Code changes in ripik-kafka-confluent
        - Push and then pull on EC2 (every ubuntu screen session, currently 4)
        - Restart the script