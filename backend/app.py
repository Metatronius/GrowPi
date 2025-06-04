from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
from meters import temp, rh, wtemp, ph
from gpiozero import MCP3008
from controls import plug
import asyncio

app = Flask(__name__, static_folder='../frontend/dist')
CORS(app)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Load pins from data.json
data = load_data()
pins = data["Sensor Pins"]

# Sensor initialization with error handling
sensor_errors = {}

def safe_init(sensor_class, *args, name=None):
    try:
        return sensor_class(*args), None
    except Exception as e:
        sensor_errors[name] = str(e)
        return None, str(e)

def safe_read(sensor, method, error_msg):
    if sensor is None:
        return {"error": error_msg}
    try:
        return getattr(sensor, method)()
    except Exception as e:
        return {"error": f"Read failed: {e}"}

@app.route('/api/status')
def status():
    return jsonify({
        "temperature": safe_read(temp_sensor, "read_temp", temp_error or sensor_errors.get("temperature", "Temperature sensor not available")),
        "humidity": safe_read(rh_sensor, "read_rh", rh_error or sensor_errors.get("humidity", "Humidity sensor not available")),
        "ph": safe_read(ph_sensor, "read_ph", ph_error or sensor_errors.get("ph", "pH sensor not available")),
        "wtemp": safe_read(wtemp_sensor, "read_temp", wtemp_error or sensor_errors.get("water_temperature", "Water temperature sensor not available"))
    })

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), path)

@app.route('/favicon.ico')
def serve_favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

@app.route('/meters')
def get_meters():
    return jsonify({
        "Air Temperature": {
            "value": safe_read(temp_sensor, "read_temp", temp_error or sensor_errors.get("temperature", "Temperature sensor not available")),
            "unit": "°F"
        },
        "Relative Humidity": {
            "value": safe_read(rh_sensor, "read_rh", rh_error or sensor_errors.get("humidity", "Humidity sensor not available")),
            "unit": "%"
        },
        "Water Temperature": {
            "value": safe_read(wtemp_sensor, "read_temp", wtemp_error or sensor_errors.get("water_temperature", "Water temperature sensor not available")),
            "unit": "°F"
        },
        "Water pH": {
            "value": safe_read(ph_sensor, "read_ph", ph_error or sensor_errors.get("ph", "pH sensor not available")),
            "unit": "pH"
        }
    })

@app.route('/controls', methods=['POST'])
def controls():
    payload = request.json or {}
    stage = payload.get("stage", "Vegetative")
    light_state = payload.get("light_state", "Lights On")

    data = load_data()
    ideal = data["Ideal Ranges"][stage]
    kasa = data["Kasa configs"]
    device_ips = kasa["Device_IPs"]
    user = kasa["Username"]
    pwd = kasa["Password"]

    temp_val = safe_read(temp_sensor, "read_temp", temp_error or sensor_errors.get("temperature", "Temperature sensor not available"))
    rh_val = safe_read(rh_sensor, "read_rh", rh_error or sensor_errors.get("humidity", "Humidity sensor not available"))

    # If either sensor failed, return error
    if isinstance(temp_val, dict) or isinstance(rh_val, dict):
        return jsonify({
            "temperature": temp_val,
            "humidity": rh_val,
            "actions": ["Cannot control devices: sensor(s) unavailable."]
        })

    temp_range = ideal["Air Temperature"][light_state]
    rh_range = ideal["Relative Humidity"]

    actions = []

    async def control_devices():
        # Fan logic
        if temp_val > temp_range["max"]:
            await plug.turnOn(device_ips["Fan"], user, pwd)
            actions.append("Fan ON (temp too high)")
        elif temp_val < temp_range["min"]:
            await plug.turnOff(device_ips["Fan"], user, pwd)
            actions.append("Fan OFF (temp too low)")
        else:
            await plug.turnOff(device_ips["Fan"], user, pwd)
            actions.append("Fan OFF (temp ideal)")

        # Humidifier logic
        if rh_val < rh_range["min"]:
            await plug.turnOn(device_ips["Humidifier"], user, pwd)
            actions.append("Humidifier ON (RH too low)")
        elif rh_val > rh_range["max"]:
            if temp_val > temp_range["min"]:
                await plug.turnOn(device_ips["Fan"], user, pwd)
                actions.append("Fan ON (RH too high, temp ok)")
            else:
                await plug.turnOff(device_ips["Fan"], user, pwd)
                actions.append("Fan OFF (RH too high, temp too low)")
            await plug.turnOff(device_ips["Humidifier"], user, pwd)
            actions.append("Humidifier OFF (RH too high)")
        else:
            await plug.turnOff(device_ips["Humidifier"], user, pwd)
            actions.append("Humidifier OFF (RH ideal)")

    asyncio.run(control_devices())

    return jsonify({
        "temperature": temp_val,
        "humidity": rh_val,
        "actions": actions
    })

@app.route('/get', methods=['GET'])
def get_data():
    data = load_data()
    return jsonify(data)

@app.route('/set', methods=['POST'])
def set_ideal_ranges():
    payload = request.json
    stage = payload.get("stage")
    meter = payload.get("meter")
    subkey = payload.get("subkey")
    values = payload.get("values")

    data = load_data()
    if stage in data["Ideal Ranges"]:
        if meter in data["Ideal Ranges"][stage]:
            if isinstance(data["Ideal Ranges"][stage][meter], dict) and subkey:
                if subkey in data["Ideal Ranges"][stage][meter]:
                    data["Ideal Ranges"][stage][meter][subkey].update(values)
            else:
                data["Ideal Ranges"][stage][meter].update(values)
    save_data(data)
    return jsonify(data["Ideal Ranges"][stage])

@app.route('/set_Pins', methods=['POST'])
def set_pins():
    new_pins = request.json
    data = load_data()
    for sensor, pin in new_pins.items():
        if sensor in data["Sensor Pins"]:
            data["Sensor Pins"][sensor] = pin
    save_data(data)
    # Re-initialize sensors with new pins
    pins = data["Sensor Pins"]
    global temp_sensor, rh_sensor, wtemp_sensor, ph_sensor, temp_error, rh_error, wtemp_error, ph_error
    sensor_errors.clear()
    temp_sensor, temp_error = safe_init(temp.TemperatureSensor, name="temperature")
    rh_sensor, rh_error = safe_init(rh.RHMeter, name="humidity")
    wtemp_sensor, wtemp_error = safe_init(wtemp.WaterTemperatureSensor, name="water_temperature")
    ph_sensor, ph_error = safe_init(ph.PHMeter, pins["Water pH Sensor"], name="ph")
    return jsonify({"message": "Pins updated and sensors re-initialized."})

@app.route('/set_Kasa', methods=['POST'])
def set_kasa():
    new_kasa = request.json
    data = load_data()
    if "Kasa configs" in data:
        data["Kasa configs"].update(new_kasa)
    save_data(data)
    return jsonify({"message": "Kasa configuration updated successfully."})

@app.route('/find_kasa', methods=['GET'])
def find_kasa():
    data = load_data()
    fan_ip = plug.get_Device_IP(data["Kasa configs"]["Username"], data["Kasa configs"]["Password"], "Fan")
    light_ip = plug.get_Device_IP(data["Kasa configs"]["Username"], data["Kasa configs"]["Password"], "Light")
    humidifier_ip = plug.get_Device_IP(data["Kasa configs"]["Username"], data["Kasa configs"]["Password"], "Humidifier")
    return jsonify({
        "Fan": fan_ip,
        "Light": light_ip,
        "Humidifier": humidifier_ip
    })

@app.route('/set_stage', methods=['POST'])
def set_stage():
    payload = request.json
    stage = payload.get("stage")
    data = load_data()
    if stage and stage in data["Ideal Ranges"]:
        data["State"]["Current Stage"] = stage
        save_data(data)
        return jsonify({"message": f"Stage set to {stage}."})
    return jsonify({"error": "Invalid stage."}), 400

IS_DEV = os.environ.get("GROWPI_DEV", "0") == "1"

if IS_DEV:
    temp_sensor, temp_error = None, "Temperature sensor not available (mocked)"
    rh_sensor, rh_error = None, "Humidity sensor not available (mocked)"
    wtemp_sensor, wtemp_error = None, "Water temperature sensor not available (mocked)"
    ph_sensor, ph_error = None, "pH sensor not available (mocked)"
else:
    temp_sensor, temp_error = safe_init(temp.TemperatureSensor, name="temperature")
    rh_sensor, rh_error = safe_init(rh.RHMeter, name="humidity")
    wtemp_sensor, wtemp_error = safe_init(wtemp.WaterTemperatureSensor, name="water_temperature")
    ph_sensor, ph_error = safe_init(ph.PHMeter, pins["Water pH Sensor"], name="ph")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
