from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
from meters import temp, rh, wtemp, ph
from gpiozero import MCP3008
from controls import plug
import asyncio
# Initialize Flask app

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
temp_sensor = temp.TemperatureSensor()
rh_sensor = rh.RHMeter()
wtemp_sensor = wtemp.WaterTemperatureSensor()
ph_sensor = ph.PHMeter(pins["Water pH Sensor"])

@app.route('/api/status')
def status():
    return jsonify({
        "temperature": temp_sensor.read_temp(),
        "humidity": rh_sensor.read_rh(),
        "ph": ph_sensor.read_ph(),
        "wtemp": wtemp_sensor.read_temp()
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
    meters= {
        "Air Temperature": {"value": temp.read_temp(), "unit": "°F"},
        "Relative Humidity": {"value": rh.read_rh(), "unit": "%"},
        "Water Temperature": {"value": wtemp.read_temp(), "unit": "°F"},
        "Water pH": {"value": ph.read_ph(), "unit": "pH"},
    }
    return jsonify(meters)

@app.route('/controls', methods=['POST'])
def controls():
    # Get current stage and light state from the request or default to "Vegetative"/"Lights On"
    payload = request.json or {}
    stage = payload.get("stage", "Vegetative")
    light_state = payload.get("light_state", "Lights On")

    data = load_data()
    ideal = data["Ideal Ranges"][stage]
    kasa = data["Kasa configs"]
    device_ips = kasa["Device_IPs"]
    user = kasa["Username"]
    pwd = kasa["Password"]

    # Read sensors
    temp_val = temp.read_temp()
    rh_val = rh.read_rh()

    # Get ideal temp and rh
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
            # Only turn on fan for high RH if temp is not too low
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
    subkey = payload.get("subkey")  # For nested keys like "Lights On"
    values = payload.get("values")   # Dict with min/max/target

    data = load_data()
    if stage in data["Ideal Ranges"]:
        if meter in data["Ideal Ranges"][stage]:
            if isinstance(data["Ideal Ranges"][stage][meter], dict) and subkey:
                # Nested (e.g., Air Temperature -> Lights On)
                if subkey in data["Ideal Ranges"][stage][meter]:
                    data["Ideal Ranges"][stage][meter][subkey].update(values)
            else:
                # Flat (e.g., Relative Humidity)
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
    global temp, rh, wtemp, ph
    temp = temp.TemperatureSensor(pins["Air Temperature Sensor"])
    rh = rh.RHMeter(pins["Relative Humidity Sensor"])
    wtemp = wtemp.WaterTemperatureSensor(pins["Water Temperature Sensor"])
    ph = ph.PHMeter(pins["Water pH Sensor"])
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
    fan_ip=plug.get_Device_IP(data["Kasa configs"]["Username"], data["Kasa configs"]["Password"], "Fan")
    light_ip=plug.get_Device_IP(data["Kasa configs"]["Username"], data["Kasa configs"]["Password"], "Light")
    humidifier_ip=plug.get_Device_IP(data["Kasa configs"]["Username"], data["Kasa configs"]["Password"], "Humidifier")
    return jsonify({
        "Fan": fan_ip,
        "Light": light_ip,
        "Humidifier": humidifier_ip
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
