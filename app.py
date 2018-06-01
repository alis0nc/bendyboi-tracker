OPTIONS = {
    # Bus numbers to track.
    'busNumbers': [3732, 3002],
    # SMART API endpoint.
    'apiEndpoint': 'https://www.smartbus.org/DesktopModules/Smart.Endpoint/proxy.ashx',
    # Polling interval, in seconds.
    'interval': 300,
}

import urllib.request, json
from collections import deque

# This could be extractable and reusable, if I cared enough, but I don't, right now.
class SmartBusAPI(object):
    def __init__(self, apiEndpoint = 'https://www.smartbus.org/DesktopModules/Smart.Endpoint/proxy.ashx'):
        self.apiEndpoint = apiEndpoint

    def getPredictions(self, bus):
        apiurl = self.apiEndpoint + "?method=predictionsforbus&vid=" + str(bus)
        data = None
        with urllib.request.urlopen(apiurl) as url:
            data = json.load(url)
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
        print(self.notify)

if __name__ == '__main__':
    api = SmartBusAPI(OPTIONS.get('apiEndpoint', None))
    tracker = BendyboiTracker(OPTIONS.get('busNumbers'), api)
    tracker.run()

