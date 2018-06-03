#!/usr/bin/env python3
OPTIONS = {
    # Bus numbers to track.
    'busNumbers': [3001, 3002, 3732, 3768, 3770, 3619],
    # SMART API endpoint.
    'apiEndpoint': 'https://www.smartbus.org/DesktopModules/Smart.Endpoint/proxy.ashx',
    # Polling interval, in seconds.
    'interval': 300,
}

import urllib.request, json, discord, asyncio, datetime
from collections import deque
from creds import CREDS

# This could be extractable and reusable, if I cared enough, but I don't, right now.
class SmartBusAPI(object):
    def __init__(self, apiEndpoint = 'https://www.smartbus.org/DesktopModules/Smart.Endpoint/proxy.ashx'):
        self.apiEndpoint = apiEndpoint

    def getPredictions(self, bus):
        apiurl = self.apiEndpoint + "?method=predictionsforbus&vid=" + str(bus)
        data = None
        try:
            with urllib.request.urlopen(apiurl) as url:
                data = json.load(url)
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
    def __init__(self, busid, route, routeName, direction, firstStop, predictedTime):
        self.busid = busid
        self.route = route
        self.routeName = routeName
        self.direction = direction
        self.firstStop = firstStop
        self.predictedTime = predictedTime

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Bus " + str(self.busid) \
          + " is heading to route " + str(self.route) \
          + " " + self.direction + " " + self.routeName + ". " \
          + "First stop " + self.firstStop + " at " + self.predictedTime

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
            r = api.getPredictions(busid)
            r = r.get('bustime-response', None)
            if r and r.get('error', None) and self.busesOnline[busid]: # bus is offline now and was online the last time we checked
                self.busesOnline[busid] = False
                self.notify.append(OfflineNotification(busid))
            elif r and r.get('error', None): # bus is offline and was the last time we checked
                pass
            elif r and not self.busesOnline[busid]: # bus is online and wasn't the last time we checked
                self.busesOnline[busid] = True
                firstPrediction = r['prd'][0]
                route = firstPrediction['rt']
                routeName = firstPrediction['des']
                direction = firstPrediction['rtdir']
                firstStop = firstPrediction['stpnm']
                predictedTime = firstPrediction['prdtm']
                self.notify.append(OnlineNotification(busid, route, routeName, direction, firstStop, predictedTime))
            elif r: # bus is online and was the last time we checked
                pass
            else: # we didn't even get a valid API response
                pass

client = discord.Client()
async def trackBuses(tracker, cid, interval):
    await client.wait_until_ready()
    channel = discord.Object(id=cid)
    while not client.is_closed:
        print(datetime.datetime.now().strftime('%H:%M:%S') + ': Running tracker')
        tracker.run()
        while tracker.notify:
            await client.send_message(channel, tracker.notify.popleft())
        await asyncio.sleep(interval)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('----------------')


api = SmartBusAPI(OPTIONS.get('apiEndpoint', None))
tracker = BendyboiTracker(OPTIONS.get('busNumbers', None), api)
client.loop.create_task(trackBuses(tracker, CREDS.get('channelID', None), OPTIONS.get('interval', 60)))
client.run(CREDS.get('token'))
