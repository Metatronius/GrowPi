from gpiozero import *
import time

analog_input = MCP3008(channel=0)
dig_in=GPIODevice(27)

def readQual():
    reading = analog_input.value
    return reading
def readQualDig():
    reading=dig_in.value
    return reading
pasDig=readQualDig()
pastQual=readQual()
while True:
    qual=readQual()
    if qual != pastQual:
        pasQual=qual
        print(passQual)
    if readQualDig() != pasDig:
        pasDig=readQualDig()
        print(pasDig)
    time.sleep(1)
