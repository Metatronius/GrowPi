import asyncio
from kasa import Discover

async def findDeviceIps(usern, pas):
    dev = await Discover.discover(username=str(usern), password=str(pas))
    return [device.host for device in dev.values()]

async def get_Device_IP(usern, pas, name):
    ips = await findDeviceIps(usern, pas)
    for ip in ips:
        device = await Discover.discover_single(str(ip), username=str(usern), password=str(pas))
        await device.update()
        if device.alias == name:
            return ip
    return None
    
async def turnOn(ip,usern,pas):
    dev = await Discover.discover_single(str(ip),username=str(usern),password=str(pas))
    await dev.turn_on()
    await dev.update()

async def turnOff(ip,usern,pas):
    dev = await Discover.discover_single(str(ip),username=str(usern),password=str(pas))
    await dev.turn_off()
    await dev.update()

async def turnToggle(ip,usern,pas):
    dev= await Discover.discover_single(str(ip),username=str(usern),password=str(pas))
    if dev.is_on():
        await dev.turn_off()
    else:
        await dev.turn_on()
    await dev.update