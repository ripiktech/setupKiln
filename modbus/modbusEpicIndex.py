import base64, requests, json, logging, os, time, math
from datetime import datetime, timedelta
from bson import json_util
from enum import Enum
from logging.handlers import TimedRotatingFileHandler

class ModbusValues(Enum):
    PLANT_NAME = "pali"
    PLANT_MODBUS = [
        {"insert": True, "data_key":"index", "plant_line": 1, "modbus_ip": "192.168.1.50", "ao_line": "AO1"},
        {"insert": False, "data_key":"index", "plant_line": 2, "modbus_ip": "192.168.1.50", "ao_line": "AO0"},
        {"insert": False, "data_key":"dusty", "plant_line": 1, "modbus_ip": "192.168.0.11"},
    ]
    ADAM_USER = "root"
    ADMAN_PASSWORD = "00000000"
    MINUTES_FOR_DATA = 30
    SCALING_FACTOR_AO = 409
    TIMEOUT = 10
    SLEEP_TIME = 120
    
class Modbus():
    
    def __init__(self) -> None:
        self.plant_name = ModbusValues.PLANT_NAME.value
        self.plant_modbus = ModbusValues.PLANT_MODBUS.value
        self.adam_user = ModbusValues.ADAM_USER.value
        self.adam_password = ModbusValues.ADMAN_PASSWORD.value
        self.minutes_for_data = ModbusValues.MINUTES_FOR_DATA.value
        self.scaling_factor_ao = ModbusValues.SCALING_FACTOR_AO.value
        self.timeout = ModbusValues.TIMEOUT.value
        self.sleep_time = ModbusValues.SLEEP_TIME.value
        self.curr_session_filename = ""
        self.logger = None
        self.make_dir()

    def make_dir(self):
        os.makedirs('logs', exist_ok=True)
        os.makedirs(f"logs/{os.path.splitext(os.path.basename(__file__))[0]}", exist_ok=True)

        log_file_name = f"logs/{os.path.splitext(os.path.basename(__file__))[0]}/{datetime.now().date()}.log"

        handler = TimedRotatingFileHandler(
            log_file_name, when="midnight", interval=1
        )

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        self.logger = logger

    def modbus_headers(self, ):
        credentials = f"{self.adam_user}:{self.adam_password}"

        base64EncodedCredentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Content-Type': 'application/xml',
            'Authorization': f'Basic {base64EncodedCredentials}'
        }
        return headers

    def parse_json(self, data):
        return json.loads(json_util.dumps(data))

    def custom_round(self, number):
        ceil_number = math.ceil(number)
        floor_number = math.floor(number)
        return ceil_number if ceil_number - number <= 0.5 else floor_number

    def calc_hex(self, response, key):
        try:
            totalIndex, i = 0, 0
            for prev_elem in response.json():
                i += 1
                totalIndex += int(prev_elem[key])
                if i >= 20:
                    break
            finalIndex = self.custom_round(totalIndex / i)
            if finalIndex > 0:
                hexNumber = hex(int(finalIndex * self.scaling_factor_ao))
                return [hexNumber, True]
            else:
                return ['00000', False]
        except Exception as e:
            self.logger.error(f"Error in calc_hex: {e}")
            hexNumber = hex(0)
            return hexNumber
        
    def input_data(self):
        status = False
        try:
            current_time = datetime.now()
            startTime = str((current_time - timedelta(minutes=self.minutes_for_data)).timestamp() * 1000)[:10] + "000"
            endTime = str(current_time.timestamp() * 1000)[:10] + "000"
            for value in self.plant_modbus:
                do_insert = value["insert"]
                if do_insert:
                    plant_line = value["plant_line"]
                    modbus_ip = value["modbus_ip"]
                    data_key = value["data_key"]
                    ao_line = value["ao_line"]
                    urlData = f"https://ultratech-ripik.com/images/index-list/?plant_name={self.plant_name}&line={plant_line}&start_time={startTime}&end_time={endTime}"
                    self.logger.info(f"Fetching data from URL: {urlData}")
                    calc_hex_output = ['00000', False]
                    try:
                        response = requests.get(urlData, headers={}, timeout=self.timeout)
                        response.raise_for_status()
                        calc_hex_output = self.calc_hex(response, data_key)
                    except Exception as e:
                        self.logger.error(f"No data found: {e}")
                    hexNumber = calc_hex_output[0]
                    dataPresent = calc_hex_output[1]
                    if dataPresent:
                        payload = f"{ao_line}=0{hexNumber[2:]}"
                    else:
                        payload = f"{ao_line}=0000"
                    self.logger.info(f"Calculated Payload for AO line: {ao_line}: {payload} for {self.plant_name} camera line: {plant_line}")
                    try:
                        url = f"http://{modbus_ip}/analogoutput/all/value"
                        headers_modbus = self.modbus_headers()
                        response = requests.post(url=url, headers=headers_modbus, data=payload, timeout=self.timeout)
                        if response.status_code == 200:
                            status = True
                            print(f"Written values for AO line: {ao_line}: {payload} for {self.plant_name} camera line: {plant_line}")
                        else:
                            print(f"ISSUE IN MODBUS IP Could not write data for: {ao_line}: {payload} for {self.plant_name} camera line: {plant_line}")
                            
                    except Exception as e:
                        self.logger.error(f"Error in POST request for AO line {ao_line}: {e} for {self.plant_name} camera line: {plant_line}")
                    self.logger.info(f"POST Response Status: {response.status_code}, Content: {response.content}")
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            print(f"Request failed: {e}")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            print(f"An error occurred: {e}")
        print(f"All Data Written Status: {status} (If false issue in modbus ip) at last run time: {datetime.now()}")
        for i in range(0, self.sleep_time):
            time.sleep(1)
            if i%30 == 0:
                print("If a new print statement is not within 40 seconds, contact developer")
                print(f"Next run in {self.sleep_time - i}")
        print("Next Run Initiated")

if __name__ == "__main__":
    modbus = Modbus()
    while True:
        modbus.input_data()
