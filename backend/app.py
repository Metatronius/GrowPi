from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
from meters import temp, rh, wtemp, ph
from gpiozero import MCP3008
from controls import plug
import asyncio
import threading
import time
import smtplib
from email.mime.text import MIMEText
from kasa import SmartPlug
import datetime
import math

app = Flask(__name__, static_folder='../frontend/dist')
CORS(app)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    print("Saving data.json with Light Schedule:", data.get("Light Schedule"))
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

# --- Kasa Plug Status Caching ---
plug_status_cache = {
    "Fan": {"status": None, "timestamp": 0},
    "Humidifier": {"status": None, "timestamp": 0},
    "Light": {"status": None, "timestamp": 0}
}
PLUG_CACHE_SECONDS = 5  # Cache duration in seconds

async def async_get_plug_status(ip):
    try:
        plug = SmartPlug(ip)
        await plug.update()
        return plug.is_on
    except Exception:
        return None

def get_plug_status_cached(name, ip):
    now = time.time()
    cache = plug_status_cache.get(name)
    if cache and (now - cache["timestamp"] < PLUG_CACHE_SECONDS):
        return cache["status"]
    # Query plug asynchronously and update cache
    try:
        status = asyncio.run(async_get_plug_status(ip))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        status = loop.run_until_complete(async_get_plug_status(ip))
    plug_status_cache[name] = {"status": status, "timestamp": now}
    return status

# --- Sensor Initialization ---
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
    ph_cal = data.get("PH Calibration", {"slope": -5.6548, "intercept": 15.509})
    ph_sensor, ph_error = safe_init(
        ph.PHMeter,
        pins["Water pH Sensor"],
        ph_cal["slope"],
        ph_cal["intercept"],
        name="ph"
    )

# --- Background Thread for pH Monitoring ---
def send_email(subject, body):
    data = load_data()
    email_settings = data.get("Email Settings", {})
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email_settings.get("from_email", "")
    msg['To'] = email_settings.get("to_email", "")

    with smtplib.SMTP(email_settings.get("smtp_server", ""), int(email_settings.get("smtp_port", 587))) as server:
        server.starttls()
        server.login(email_settings.get("username", ""), email_settings.get("password", ""))
        server.send_message(msg)

def ph_monitor_loop():
    while True:
        try:
            ph_value = safe_read(ph_sensor, "read_ph", ph_error or sensor_errors.get("ph", "pH sensor not available"))
            data = load_data()
            stage = data["State"]["Current Stage"]
            ph_range = data["Ideal Ranges"][stage]["Water pH"]
            min_ph = ph_range["min"]
            max_ph = ph_range["max"]
            if isinstance(ph_value, (int, float)) and (ph_value < min_ph or ph_value > max_ph):
                send_email(
                    subject="GrowPi Alert: pH Out of Range",
                    body=f"Current pH is {ph_value:.2f}, which is outside the ideal range ({min_ph}-{max_ph}).",
                    to_email=data.get("Email Settings", {}).get("to_email", "")
                )
        except Exception as e:
            print(f"pH monitor error: {e}")
        time.sleep(4 * 60 * 60)  # 4 hours

threading.Thread(target=ph_monitor_loop, daemon=True).start()

# --- Climate and Light Control ---

def run_climate_and_light_control():
    data = load_data()
    stage = data["State"]["Current Stage"]
    light_state = "Lights On"  # Or determine based on schedule
    ideal = data["Ideal Ranges"][stage]
    kasa = data["Kasa configs"]
    device_ips = kasa["Device_IPs"]
    user = kasa["Username"]
    pwd = kasa["Password"]

    units = data.get("Units", {})
    humidity_metric = units.get("Humidity Metric", "RH")
    temp_unit = units.get("Temperature", "F")

    temp_val = safe_read(temp_sensor, "read_temp", temp_error or sensor_errors.get("temperature", "Temperature sensor not available"))
    rh_val = safe_read(rh_sensor, "read_rh", rh_error or sensor_errors.get("humidity", "Humidity sensor not available"))

    temp_range = ideal["Air Temperature"][light_state]

    if humidity_metric == "VPD" and isinstance(temp_val, (int, float)) and isinstance(rh_val, (int, float)):
        temp_c = temp_val if temp_unit == "C" else to_celsius(temp_val)
        humidity_val = calculate_vpd(temp_c, rh_val)
        hum_range = ideal.get("VPD", {"min": 0.8, "max": 1.2, "target": 1.0})
    else:
        humidity_val = rh_val
        hum_range = ideal.get("Relative Humidity", {"min": 40, "max": 60, "target": 50})

    actions = []

    async def control_devices():
        fan_on = True  # Default: keep fan ON
        humid_on = False
        dehumid_on = False
        heater_on = False

        # --- Fan logic ---
        if humidity_metric == "VPD":
            # Fan ON if temp > min and VPD < max (humid, needs drying)
            if temp_val > temp_range["min"] and humidity_val < hum_range["max"]:
                fan_on = True
                actions.append("Fan ON (temp > min and VPD < max: air humid, drying)")
            else:
                fan_on = False
                actions.append("Fan OFF (temp <= min or VPD >= max: air dry or temp low)")
        else:
            # Original logic for RH
            if temp_val < temp_range["min"]:
                fan_on = False
                actions.append("Fan OFF (temp too low)")
            else:
                fan_on = True
                actions.append("Fan ON (temp at/above min)")

        # Humidifier logic (fix for VPD)
        if humidity_metric == "VPD":
            # For VPD, high value = low RH (too dry), so turn ON humidifier if VPD > max
            if humidity_val > hum_range["max"]:
                humid_on = True
                actions.append("Humidifier ON (VPD too high, air too dry)")
            else:
                humid_on = False
                actions.append("Humidifier OFF (VPD ok or too low)")
            # For dehumidifier, turn ON if VPD < min (too humid)
            if "Dehumidifier" in device_ips:
                if humidity_val < hum_range["min"]:
                    dehumid_on = True
                    actions.append("Dehumidifier ON (VPD too low, air too humid)")
                else:
                    dehumid_on = False
                    actions.append("Dehumidifier OFF (VPD ok or too high)")
        else:
            # RH logic (original)
            if humidity_val < hum_range["min"]:
                humid_on = True
                actions.append("Humidifier ON (RH too low)")
            else:
                humid_on = False
                actions.append("Humidifier OFF (RH ok or too high)")
            if "Dehumidifier" in device_ips:
                if humidity_val > hum_range["max"]:
                    dehumid_on = True
                    actions.append("Dehumidifier ON (RH too high)")
                else:
                    dehumid_on = False
                    actions.append("Dehumidifier OFF (RH ok or too low)")

        # --- Dehumidifier logic ---
        if "Dehumidifier" in device_ips:
            if humidity_val > hum_range["max"]:
                dehumid_on = True
                actions.append("Dehumidifier ON (humidity too high)")
            elif humidity_val <= hum_range["target"]:
                dehumid_on = False
                actions.append("Dehumidifier OFF (humidity at/below target)")
            else:
                actions.append("Dehumidifier state unchanged")

        # --- Heater logic ---
        # Turn ON if temp < min, OFF if >= target
        if "Heater" in device_ips:
            if temp_val < temp_range["min"]:
                heater_on = True
                actions.append("Heater ON (temp too low)")
            elif temp_val >= temp_range["target"]:
                heater_on = False
                actions.append("Heater OFF (temp at/above target)")
            else:
                actions.append("Heater state unchanged")

        # --- Apply actions to plugs ---
        if "Fan" in device_ips:
            if fan_on:
                await plug.turnOn(device_ips["Fan"], user, pwd)
            else:
                await plug.turnOff(device_ips["Fan"], user, pwd)
        if "Humidifier" in device_ips:
            if humid_on:
                await plug.turnOn(device_ips["Humidifier"], user, pwd)
            else:
                await plug.turnOff(device_ips["Humidifier"], user, pwd)
        if "Dehumidifier" in device_ips:
            if dehumid_on:
                await plug.turnOn(device_ips["Dehumidifier"], user, pwd)
            else:
                await plug.turnOff(device_ips["Dehumidifier"], user, pwd)
        if "Heater" in device_ips:
            if heater_on:
                await plug.turnOn(device_ips["Heater"], user, pwd)
            else:
                await plug.turnOff(device_ips["Heater"], user, pwd)

        # --- Light schedule logic ---
        now = datetime.datetime.now().time()
        light_sched = data.get("Light Schedule", {"on": "06:00", "off": "22:00"})
        on_time = datetime.datetime.strptime(light_sched["on"], "%H:%M").time()
        off_time = datetime.datetime.strptime(light_sched["off"], "%H:%M").time()

        # Handle overnight schedules
        if on_time < off_time:
            light_should_be_on = on_time <= now < off_time
        else:
            light_should_be_on = now >= on_time or now < off_time

        # Query current light state
        try:
            current_light_state = await async_get_plug_status(device_ips["Light"])
        except Exception:
            current_light_state = None

        if light_should_be_on and not current_light_state:
            await plug.turnOn(device_ips["Light"], user, pwd)
            actions.append("Light ON (according to schedule)")
        elif not light_should_be_on and current_light_state:
            await plug.turnOff(device_ips["Light"], user, pwd)
            actions.append("Light OFF (according to schedule)")
        else:
            actions.append(f"Light {'ON' if current_light_state else 'OFF'} (already correct)")

    asyncio.run(control_devices())
    return actions

# Background thread to run every 5 minutes
def climate_and_light_loop():
    while True:
        try:
            actions = run_climate_and_light_control()
            print(f"[{datetime.datetime.now()}] Climate/Light actions: {actions}")
        except Exception as e:
            print(f"Climate/Light control error: {e}")
        time.sleep(5 * 60)

threading.Thread(target=climate_and_light_loop, daemon=True).start()

# --- Utility Functions ---

def to_celsius(f):
    return (f - 32) * 5.0 / 9.0

def to_24h(time_str):
    return time_str

def to_12h(time_str):
    hour, minute = map(int, time_str.split(":"))
    ampm = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:{minute:02d} {ampm}"

def calculate_vpd(temp_c, rh):
    svp = 0.61078 * math.exp(17.27 * temp_c / (temp_c + 237.3))
    avp = svp * (rh / 100.0)
    vpd = svp - avp
    return round(vpd, 3)

# --- Flask Routes ---

@app.route('/api/status')
def status():
    data = load_data()
    device_ips = data["Kasa configs"]["Device_IPs"]
    units = data.get("Units", {})
    temp_unit = units.get("Temperature", "F")
    time_unit = units.get("Time", "12h")
    humidity_metric = units.get("Humidity Metric", "RH")
    stage = data["State"].get("Current Stage")
    ideal = data["Ideal Ranges"].get(stage, {}) if stage else {}

    temp_val = safe_read(temp_sensor, "read_temp", temp_error or sensor_errors.get("temperature", "Temperature sensor not available"))
    rh_val = safe_read(rh_sensor, "read_rh", rh_error or sensor_errors.get("humidity", "Humidity sensor not available"))
    wtemp_val = safe_read(wtemp_sensor, "read_temp", wtemp_error or sensor_errors.get("water_temperature", "Water temperature sensor not available"))

    # Convert temperature if needed
    if temp_unit == "C" and isinstance(temp_val, (int, float)):
        temp_val = round(to_celsius(temp_val), 2)
    if temp_unit == "C" and isinstance(wtemp_val, (int, float)):
        wtemp_val = round(to_celsius(wtemp_val), 2)

    # Calculate VPD if needed
    if humidity_metric == "VPD" and isinstance(temp_val, (int, float)) and isinstance(rh_val, (int, float)):
        temp_c = temp_val if temp_unit == "C" else to_celsius(temp_val)
        humidity_val = calculate_vpd(temp_c, rh_val)
        hum_range = ideal.get("VPD", {"min": 0.8, "max": 1.2, "target": 1.0})
    else:
        humidity_val = rh_val
        hum_range = ideal.get("Relative Humidity", {"min": 40, "max": 60, "target": 50})

    # Light schedule formatting
    light_sched = data.get("Light Schedule", {"on": "06:00", "off": "22:00"})
    if time_unit == "24h":
        light_on = light_sched["on"]
        light_off = light_sched["off"]
    else:
        light_on = to_12h(light_sched["on"])
        light_off = to_12h(light_sched["off"])

    return jsonify({
        "temperature": temp_val,
        "humidity": humidity_val,
        "humidity_metric": humidity_metric,
        "hum_range": hum_range,
        "ph": safe_read(ph_sensor, "read_ph", ph_error or sensor_errors.get("ph", "pH sensor not available")),
        "wtemp": wtemp_val,
        "fan_status": get_plug_status_cached("Fan", device_ips.get("Fan", "")),
        "humidifier_status": get_plug_status_cached("Humidifier", device_ips.get("Humidifier", "")),
        "light_status": get_plug_status_cached("Light", device_ips.get("Light", "")),
        "light_on": light_on,
        "light_off": light_off
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
    actions = run_climate_and_light_control()
    temp_val = safe_read(temp_sensor, "read_temp", temp_error or sensor_errors.get("temperature", "Temperature sensor not available"))
    rh_val = safe_read(rh_sensor, "read_rh", rh_error or sensor_errors.get("humidity", "Humidity sensor not available"))
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
    pins = data["Sensor Pins"]
    global temp_sensor, rh_sensor, wtemp_sensor, ph_sensor, temp_error, rh_error, wtemp_error, ph_error
    sensor_errors.clear()
    temp_sensor, temp_error = safe_init(temp.TemperatureSensor, name="temperature")
    rh_sensor, rh_error = safe_init(rh.RHMeter, name="humidity")
    wtemp_sensor, wtemp_error = safe_init(wtemp.WaterTemperatureSensor, name="water_temperature")
    ph_cal = data.get("PH Calibration", {"slope": -5.6548, "intercept": 15.509})
    ph_sensor, ph_error = safe_init(
        ph.PHMeter,
        pins["Water pH Sensor"],
        ph_cal["slope"],
        ph_cal["intercept"],
        name="ph"
    )
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
    user = data["Kasa configs"]["Username"]
    pwd = data["Kasa configs"]["Password"]
    try:
        fan_ip = asyncio.run(plug.get_Device_IP(user, pwd, "Fan"))
        light_ip = asyncio.run(plug.get_Device_IP(user, pwd, "Light"))
        humidifier_ip = asyncio.run(plug.get_Device_IP(user, pwd, "Humidifier"))
        return jsonify({
            "Fan": fan_ip,
            "Light": light_ip,
            "Humidifier": humidifier_ip
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/set_stage', methods=['POST'])
def set_stage():
    payload = request.json
    stage = payload.get("stage")
    data = load_data()
    if stage and stage in data["Ideal Ranges"]:
        data["State"]["Current Stage"] = stage
        save_data(data)
        return jsonify({"message": f"Stage set to {stage}."})
    return jsonify({"error": "Invalid stage."}, 400)

@app.route('/light_schedule', methods=['GET'])
def get_light_schedule():
    data = load_data()
    return jsonify(data.get("Light Schedule", {}))

@app.route('/light_schedule', methods=['POST'])
def set_light_schedule():
    print("Received POST to /light_schedule")
    payload = request.json
    data = load_data()
    data["Light Schedule"] = {
        "on": payload["on"],
        "off": payload["off"]
    }
    save_data(data)
    return jsonify({"message": "Light schedule updated."})

@app.route('/ph_calibration', methods=['GET'])
def get_ph_calibration():
    data = load_data()
    return jsonify(data.get("PH Calibration", {}))

@app.route('/ph_calibration', methods=['POST'])
def set_ph_calibration():
    payload = request.json
    slope = payload.get("slope")
    intercept = payload.get("intercept")
    data = load_data()
    if slope is not None and intercept is not None:
        data["PH Calibration"] = {"slope": slope, "intercept": intercept}
        save_data(data)
        # Re-initialize pH sensor with new calibration
        pins = data["Sensor Pins"]
        global ph_sensor, ph_error
        ph_sensor, ph_error = safe_init(
            ph.PHMeter,
            pins["Water pH Sensor"],
            slope,
            intercept,
            name="ph"
        )
        return jsonify({"message": "Calibration updated."})
    return jsonify({"error": "Missing slope or intercept."}, 400)

@app.route('/ph_calibration_point', methods=['POST'])
def ph_calibration_point():
    global ph_sensor, ph_error
    payload = request.json
    known_ph = payload.get("known_ph")
    data = load_data()
    pins = data["Sensor Pins"]
    ph_adc = MCP3008(channel=pins["Water pH Sensor"])
    voltage = ph_adc.value * 3.3
    cal_points = data.setdefault("PH Calibration Points", [])
    cal_points.append({"ph": known_ph, "voltage": voltage})

    if len(cal_points) == 2:
        # Linear calibration (2-point)
        p1, p2 = cal_points
        slope = (p1["ph"] - p2["ph"]) / (p1["voltage"] - p2["voltage"])
        intercept = p1["ph"] - slope * p1["voltage"]
        data["PH Calibration"] = {"type": "linear", "slope": slope, "intercept": intercept}
        data["PH Calibration Points"] = []
        save_data(data)
        ph_sensor, ph_error = safe_init(
            ph.PHMeter,
            pins["Water pH Sensor"],
            slope,
            intercept,
            name="ph"
        )
        return jsonify({"message": f"2-point calibration complete! Slope: {slope:.4f}, Intercept: {intercept:.4f}"})
    elif len(cal_points) == 3:
        # Quadratic calibration (3-point)
        import numpy as np
        v = np.array([p["voltage"] for p in cal_points])
        phs = np.array([p["ph"] for p in cal_points])
        # Fit quadratic: ph = a*v^2 + b*v + c
        coeffs = np.polyfit(v, phs, 2)
        a, b, c = coeffs
        data["PH Calibration"] = {"type": "quadratic", "a": a, "b": b, "c": c}
        data["PH Calibration Points"] = []
        save_data(data)
        ph_sensor, ph_error = safe_init(
            ph.PHMeter,
            pins["Water pH Sensor"],
            a,
            b,
            c,
            name="ph"
        )
        return jsonify({"message": f"3-point calibration complete! a: {a:.6f}, b: {b:.6f}, c: {c:.6f}"})
    else:
        save_data(data)
        return jsonify({"message": f"Calibration point saved. Please add {2 - len(cal_points) if len(cal_points) < 2 else 3 - len(cal_points)} more point(s)."})
@app.route('/set_units', methods=['POST'])
def set_units():
    units = request.json
    data = load_data()
    prev_units = data.get("Units", {})
    # Convert temperature ranges if unit changed
    if "Temperature" in units and units["Temperature"] != prev_units.get("Temperature"):
        from_F = units["Temperature"] == "C" and prev_units.get("Temperature") == "F"
        from_C = units["Temperature"] == "F" and prev_units.get("Temperature") == "C"
        for stage, meters in data.get("Ideal Ranges", {}).items():
            for meter, value in meters.items():
                # Handle nested (e.g. Air Temperature with Lights On/Off)
                if isinstance(value, dict) and "min" in value and "max" in value and "target" in value:
                    if from_F:
                        value["min"] = round((value["min"] - 32) * 5/9, 2)
                        value["max"] = round((value["max"] - 32) * 5/9, 2)
                        value["target"] = round((value["target"] - 32) * 5/9, 2)
                    elif from_C:
                        value["min"] = round(value["min"] * 9/5 + 32, 2)
                        value["max"] = round(value["max"] * 9/5 + 32, 2)
                        value["target"] = round(value["target"] * 9/5 + 32, 2)
                # Handle Air Temperature with Lights On/Off
                elif isinstance(value, dict):
                    for subkey, subval in value.items():
                        if isinstance(subval, dict) and "min" in subval and "max" in subval and "target" in subval:
                            if from_F:
                                subval["min"] = round((subval["min"] - 32) * 5/9, 2)
                                subval["max"] = round((subval["max"] - 32) * 5/9, 2)
                                subval["target"] = round((subval["target"] - 32) * 5/9, 2)
                            elif from_C:
                                subval["min"] = round(subval["min"] * 9/5 + 32, 2)
                                subval["max"] = round(subval["max"] * 9/5 + 32, 2)
                                subval["target"] = round(subval["target"] * 9/5 + 32, 2)
    # Convert light schedule if time format changed
    if "Time" in units and units["Time"] != prev_units.get("Time"):
        sched = data.get("Light Schedule", {})
        if "on" in sched and "off" in sched:
            if units["Time"] == "24h":
                # Convert from 12h to 24h
                sched["on"] = to_24h(sched["on"])
                sched["off"] = to_24h(sched["off"])
            else:
                # Convert from 24h to 12h
                sched["on"] = to_12h(sched["on"])
                sched["off"] = to_12h(sched["off"])
            data["Light Schedule"] = sched
    data["Units"] = units
    save_data(data)
    return jsonify({"message": "Units updated and config converted."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
