# setupKiln

## Overview
This repository contains tools and configurations for setting up new camera line installations for Ultratech Kiln monitoring systems, primarily for OnPrem deployments.

## Prerequisites
- Python 3.10
- VS Code
- Chocolatey package manager
- NSSM (Non-Sucking Service Manager)
- Required Python packages (listed in requirements.txt)

## Setup Process

### Part 1: OnPrem Configuration

1. **Initial Setup**
   - Upload and extract the setupKiln folder to the target machine
   - Open the folder in VS Code

2. **Install Required Software**
   - Install Python 3.10
   - Install required Python packages:
     ```
     pip install -r requirements.txt
     ```
   - Install Chocolatey:
     - Open PowerShell as Administrator
     - Follow instructions from [Chocolatey installation website](https://chocolatey.org/install)
   - Install NSSM using Chocolatey:
     ```
     choco install nssm
     ```

3. **Configure Kafka and AWS**
   - Edit `constants.py` with appropriate Kafka and AWS configuration values

4. **Set Up Kafka Service**
   - Run the following command to create a Windows service:
     ```
     nssm install kafka
     ```
   - When prompted, select the BAT file located in the kafka folder within setupKiln
   - Edit the BAT file to use the full Python path
     - To find the full Python path:
       ```
       python
       >>> import sys
       >>> sys.path
       ```
     - Copy the correct Python path and update the BAT file

5. **Configure Camera Settings**
   - Specify RTSP URL and image upload path on S3 for the plant camera key
   - Format: `rpk-clnt-in-prd/rpkultratech/kilnhealth/<camera_key>/`
   - Update these settings in MongoDB

6. **Testing**
   - Test the BAT file by double-clicking it
   - Check logs to verify Kafka events are being produced
   - Test the Windows service and verify logs
   - Configure the Windows service to automatically restart on failure

### Part 2: Cloud Configuration

After confirming Kafka events are successfully produced:

1. **Model Configuration**
   - Specify model path for the plant camera key in MongoDB collection
   - Format: `rpk-clnt-in-prd/rpkultratech/kilnhealth/models/<camera_key>/resnet18.pth`

2. **Restart Consumers**
   - Make code changes in ripik-kafka-confluent
   - Push changes and then pull on EC2 (all Ubuntu screen sessions, currently 4)
   - Restart the script

## Troubleshooting

### Common Issues
- **Kafka events not producing**: Check network connectivity, Kafka configuration in constants.py
- **Service not starting**: Verify Python path in BAT file, check Windows Event logs
- **Image upload failures**: Verify AWS credentials and S3 bucket permissions

### Logs
- Check service logs in the application log directory
- Verify Kafka event production in the console output

## Maintenance

### Service Management
- Start service: `net start kafka`
- Stop service: `net stop kafka`
- Check service status: `sc query kafka`

## Contact

For additional support, contact the DevOps team.