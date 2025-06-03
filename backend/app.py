from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
from meters import temp, rh, wtemp, ph
from gpiozero import MCP3008
from controls import plug
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
temp = temp.TemperatureSensor(pin=pins["Air Temperature Sensor"])
rh = rh.RHMeter(pin=pins["Relative Humidity Sensor"])
wtemp = wtemp.WaterTemperatureSensor(pin=pins["Water Temperature Sensor"])
ph = ph.PHMeter(pin=pins["Water pH Sensor"])

@app.route('/api/status')
def status():
    return jsonify({
        "temperature": temp.read_temp(),
        "humidity": rh.read_rh(),
        "ph": ph.read_ph(),
        "wtemp": wtemp.read_temp()
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

@app.route('/controls')
def controls():
    # TODO: Implement controls logic or return a placeholder response
    return jsonify({"message": "Controls endpoint not implemented yet."})

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
    temp = temp.TemperatureSensor(pin=pins["Air Temperature Sensor"])
    rh = rh.RHMeter(pin=pins["Relative Humidity Sensor"])
    wtemp = wtemp.WaterTemperatureSensor(pin=pins["Water Temperature Sensor"])
    ph = ph.PHMeter(pin=pins["Water pH Sensor"])
    return jsonify({"message": "Pins updated and sensors re-initialized."})

@app.route('/set_Kasa', methods=['POST'])
def set_kasa():
    new_kasa = request.json
    data = load_data()
    if "Kasa configs" in data:
        data["Kasa configs"].update(new_kasa)
    save_data(data)
    return jsonify({"message": "Kasa configuration updated successfully."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
