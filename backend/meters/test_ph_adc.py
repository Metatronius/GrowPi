# Save as test_ph_adc.py
from gpiozero import MCP3008
import time

ph_channel = 0  # Use the same channel as in your data.json

adc = MCP3008(channel=ph_channel)

while True:
    voltage = adc.value * 3.3
    print(f"Raw ADC value: {adc.value:.3f}, Voltage: {voltage:.3f} V")
    time.sleep(1)
