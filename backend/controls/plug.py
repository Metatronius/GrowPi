import asyncio
from kasa import Discover

async def findDiviceIp(usern,pas):
    dev = await Discover.discover(username=str(usern),password=str(pas))
    lis=[]
    for devices in dev.values():
        await devices.update()
        lis.append(devices.host)
    return lis

async def get_Device_IP(usern,pas,name):
    lis =findDiviceIp(usern,pas)
    for ip in lis:
        device = await Discover.discover_single(str(ip), username=str(usern), password=str(pas))
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