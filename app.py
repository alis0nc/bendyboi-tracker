#!/usr/bin/env python3

import urllib.request, json, discord, asyncio, datetime
from collections import deque
from config import CREDS, OPTIONS
from discord.ext import commands

# This could be extractable and reusable, if I cared enough, but I don't, right now.
class SmartBusAPI(object):
    def __init__(self, apiEndpoint = 'https://www.smartbus.org/DesktopModules/Smart.Endpoint/proxy.ashx'):
        self.apiEndpoint = apiEndpoint

    def getPredictions(self, bus):
        apiurl = self.apiEndpoint + "?method=predictionsforbus&vid=" + str(bus)
        req = urllib.request.Request(
            apiurl, 
            data = None,
            headers = {
                'User-Agent': 'Bendybot/0.0.1 (https://github.com/alis0nc/bendyboi-tracker; bendyboi.tracker@alisonc.net)'
            }
        )
        data = None
        try:
            with urllib.request.urlopen(req) as u:
                data = json.load(u)
        except urllib.error.URLError:
            pass # swallow errors and pass a None up the chain
        return data

class OfflineNotification(object):
    def __init__(self, busid):
        self.busid = busid
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return "Bus " + str(self.busid) + " is now offline."

class OnlineNotification(object):
    def __init__(self, busid, route, routeName, direction, firstStop, stopId, predictedTime):
        self.busid = busid
        self.route = route
        self.routeName = routeName
        self.direction = direction
        self.firstStop = firstStop
        self.stopId = stopId
        self.predictedTime = predictedTime

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Bus " + str(self.busid) \
          + " is heading to route " + str(self.route) \
          + " " + self.direction + " " + self.routeName + ". " \
          + "First stop " + self.firstStop + " (ID " + self.stopId + ") at " + self.predictedTime

class BendyboiTracker(object):
    def __init__(self, busesToTrack = None, api = SmartBusAPI()):
        self.busesToTrack = busesToTrack
        self.api = api
        self.busesOnline = {}
        self.notify = deque()
        for busid in busesToTrack:
            self.busesOnline[busid] = False

    def run(self):
        for busid in self.busesToTrack:
            r = api.getPredictions(busid) or {}
            r = r.get('bustime-response', None)
            if r and r.get('error', None) and self.busesOnline[busid]: # bus is offline now and was online the last time we checked
                self.busesOnline[busid] = False
                self.notify.append(OfflineNotification(busid))
            elif r and r.get('error', None): # bus is offline and was the last time we checked
                pass
            elif r and r.get('prd', None) and not self.busesOnline[busid]: # bus is online and wasn't the last time we checked
                self.busesOnline[busid] = True
                try:
                    firstPrediction = r['prd'][0]
                except KeyError: # Only one prediction, so API doesn't gives us an array >(
                    firstPrediction = r['prd']
                route = firstPrediction['rt']
                routeName = firstPrediction['des']
                direction = firstPrediction['rtdir']
                firstStop = firstPrediction['stpnm']
                stopId = firstPrediction['stpid']
                predictedTime = firstPrediction['prdtm']
                self.notify.append(OnlineNotification(busid, route, routeName, direction, firstStop, stopId, predictedTime))
            elif r and r.get('prd', None): # bus is online and was the last time we checked
                pass
            else: # we didn't even get a valid API response
                pass

description = 'SMART bus tracker.'

client = commands.Bot(command_prefix='!', description=description)
api = SmartBusAPI(OPTIONS.get('apiEndpoint', None))
tracker = BendyboiTracker(OPTIONS.get('busNumbers', None), api)

async def trackBuses(tracker, cid, interval):
    await client.wait_until_ready()
    channel = discord.Object(id=cid)
    while not client.is_closed:
        print(datetime.datetime.now().strftime('%H:%M:%S') + ': Running tracker')
        tracker.run()
        while tracker.notify:
            await client.send_message(channel, tracker.notify.popleft())
        await asyncio.sleep(interval)

@client.command()
async def whereis(busid : int):
    """Queries the API for the location of a bus."""
    print('whereis')
    resp = api.getPredictions(busid)
    resp = resp.get('bustime-response', None)
    if resp and not resp.get('error', None):
        try:
            firstPrediction = resp['prd'][0]
        except KeyError: # Only one prediction, so API doesn't gives us an array >(
            firstPrediction = resp['prd']
        route = firstPrediction['rt']
        routeName = firstPrediction['des']
        direction = firstPrediction['rtdir']
        nextStop = firstPrediction['stpnm']
        stopId = firstPrediction['stpid']
        predictedTime = firstPrediction['prdtm']
        await client.say('Bus ' + str(busid) + ' is on ' + str(route) + ' ' + direction + ' ' \
            + routeName + '. Next stop ' + nextStop + ' (ID ' + stopId + ') at ' + predictedTime)
    else:
        await client.say('Bus ' + str(busid) + ' is currently offline.')

@client.command()
async def github():
    await client.say('https://github.com/alis0nc/bendyboi-tracker')

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('----------------')

client.loop.create_task(trackBuses(tracker, CREDS.get('channelID', None), OPTIONS.get('interval', 60)))
client.run(CREDS.get('token'))
