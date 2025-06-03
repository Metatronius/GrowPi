from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
from meters import temp, rh, wtemp, ph
from gpiozero import MCP3008
# Initialize sensors
temp = temp.TemperatureSensor(pin=0)  # Example pin
rh = rh.RHMeter(pin=1)  # Example pin
wtemp = wtemp.WaterTemperatureSensor(pin=2)  # Example pin
ph = ph.PHMeter(pin=3)  # Example pin
# Initialize Flask app

app = Flask(__name__, static_folder='../frontend/dist')
CORS(app)

@app.route('/api/status')
def status():
    return jsonify({"temperature": temp.read_temp(), "humidity": rh.read_rh()})

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

ideal_ranges = {
    "Air Temperature": {"min": 68, "max": 72, "target": 70},
    "Relative Humidity": {"min": 40, "max": 60, "target": 50},
    "Water Temperature": {"min": 70, "max": 75, "target": 72.5},
    "Water pH": {"min": 5.0, "max": 6.0, "target": 5.5},
}
@app.route('/set')
def set_ideal_ranges():
    new_ranges = request.json
    for key, value in new_ranges.items():
        if key in ideal_ranges:
            ideal_ranges[key].update(value)
    return jsonify(ideal_ranges)
@app.route('/set_Pins')
def set_pins():
    new_pins = request.json
    for sensor, pin in new_pins.items():
        if sensor == "TemperatureSensor":
            temp.pin = pin
        elif sensor == "RHMeter":
            rh.pin = pin
        elif sensor == "WaterTemperatureSensor":
            wtemp.pin = pin
        elif sensor == "PHMeter":
            ph.pin = pin
    return jsonify({"message": "Pins updated successfully."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
