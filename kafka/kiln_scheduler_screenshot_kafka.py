import logging
import os
import time
from datetime import datetime
import requests
import boto3
from kafka_init import KafkaLocalClass
from PIL import ImageGrab

plant_name = "pali1"
clientId = "ultratech"

inference_url = "https://ultratech-ripik.com/images/list/"
os.makedirs('logs', exist_ok=True)
output_dir = 'output_image'
os.makedirs(output_dir, exist_ok=True)
logging.basicConfig(
    filename= f"logs/kafka-{plant_name}-{datetime.now().date()}.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class UploadImage():
    
    def __init__(self, plant_name, client_id) -> None:
        self.plant_name = plant_name
        self.client_id = client_id
        self.camera_detail = self.get_details()
        self.rtsp_url = self.camera_detail["rtsp_url"]
        self.s3_bucket = self.camera_detail["s3_bucket"]
        self.s3_bucket_folder = self.camera_detail["s3_bucket_folder"]
        self.image_cutoff = self.camera_detail["image_cutoff"]
        self.plant_corrected_name = self.camera_detail["plant_corrected_name"]
        self.aws_account = self.camera_detail["aws_account"]
        self.inference_url = inference_url
        self.kafka = KafkaLocalClass(self.client_id, "kilnhealth")
        logging.info(f"Image collection script started for {self.plant_name} with payload: {self.camera_detail}")
        
    def get_details(self):
        camera_detail_url = f"https://ultratech-ripik.com/images/plant-camera-detail-s3/?plant_name={self.plant_name}&clientId={self.client_id}&usecase=kilnhealth&type=rtsp"
        camera_detail = requests.get(camera_detail_url)
        camera_detail = camera_detail.json()
        return camera_detail
    
    def set_details(self):
        try:
            new_details = self.get_details()
            self.rtsp_url = new_details["rtsp_url"]
            self.s3_bucket = new_details["s3_bucket"]
            self.s3_bucket_folder = new_details["s3_bucket_folder"]
            self.image_cutoff = new_details["image_cutoff"]
            self.plant_corrected_name = new_details["plant_corrected_name"]
            self.aws_account = new_details["aws_account"]
        except Exception as e:
            logging.error(f"Exception in get_details(): {e}")
        return
    
    def upload_image(self, data, name):
        try:
            s3_client = boto3.client('s3')
            s3_client.upload_fileobj(data, self.s3_bucket, name)
            image_url = f"https://{self.s3_bucket}.s3.amazonaws.com/{name}"
            logging.info(f"Successfully uploaded image {name}")
            return {"image_url": image_url, "message": True}
        except Exception as e:
            logging.error(f"Failed to upload image {name}: {e}")
            return {"image_url": None, "message": False}
    
    def capture_image(self, max_images=5, left=0, top=0, right=1920, bottom=1080):
        logging.info(f"{plant_name} Image collection script started")
        logging.info('Connecting... (Takes up to 30-40 seconds)')
        while True:
            try:
                count = 1
                session_image_count = 0
                while session_image_count < max_images:
                    logging.info("Started Loop")
                    if session_image_count >= max_images:
                        break

                    for attempt in range(3):
                        try:
                            # Capture the screen region
                            frame = ImageGrab.grab(bbox=(left, top, right, bottom))

                            # Convert to bytes and check validity
                            is_frame_valid = False
                            for _ in range(3):
                                buffer = frame.tobytes()
                                if len(buffer) < self.image_cutoff * 1024:
                                    logging.info(f"Frame size is less than 20KB. Retaking image ({_ + 1}/3)...")
                                    time.sleep(2)
                                    frame = ImageGrab.grab(bbox=(left, top, right, bottom))
                                else:
                                    is_frame_valid = True
                                    break

                            if is_frame_valid:
                                break
                            else:
                                logging.info(f"Failed to capture a valid frame. Retrying ({attempt + 1}/3)...")
                                time.sleep(2)
                        except Exception as e:
                            logging.error(f"Screenshot capture error: {e}")
                            time.sleep(2)
                            continue

                    if not is_frame_valid:
                        logging.info("Failed to capture a valid screenshot after 3 attempts.")
                        break

                    # Save the image to disk
                    current_time = datetime.now()
                    file_name = current_time.strftime(f'{count}photo_%Y-%m-%d_%H-%M-%S_{plant_name}.png')
                    image_path = os.path.join(output_dir, file_name)
                    frame.save(image_path, "PNG")

                    # Upload image and process
                    try:
                        with open(image_path, "rb") as data:
                            object_key = f"{self.s3_bucket_folder}/{file_name}"
                            uploaded_image = self.upload_image(data=data, name=object_key)
                            logging.info(f"Saved and uploaded image {uploaded_image}")
                            if uploaded_image["message"]:
                                data_to_push = {
                                    "data": {
                                        "plant_name": self.plant_name,
                                        "url": uploaded_image["image_url"],
                                        "clientId": self.client_id,
                                        "cloud": "aws",
                                        "bucket": self.s3_bucket,
                                        "object_key": object_key,
                                        "aws_account": self.aws_account,
                                        "photo_num": count,
                                        "photo_info": file_name
                                    }
                                }
                                # Kafka event production placeholder
                                generate_event = self.kafka.produce(None, data_to_push)
                                if generate_event == 200:
                                    logging.info("Event was generated successfully")
                                else:
                                    logging.error("Event was not generated")
                            else:
                                logging.error("Image couldn't be uploaded")
                                print("Issue in Image upload, please contact Ripik.ai Team")
                    except Exception as e:
                        logging.info(f"Failed to upload image {file_name}: {e}")
                    os.remove(image_path)
                    count += 1
                    session_image_count += 1
                    time.sleep(8)
            except KeyboardInterrupt:
                logging.info("Ending session...")
                break
            except Exception as e:
                logging.error(f"Unexpected Error: {e}")
                self.handle_crash()
            time.sleep(120)
            self.set_details()
    def handle_crash(self):
        time.sleep(2)
        self.capture_image()

if __name__ == "__main__":
    upload_image = UploadImage(plant_name, clientId)
    upload_image.capture_image()