# bendyboi-tracker
Discord bot that periodically pokes the https://smartbus.org/ API and sends alerts when specific buses come online

## API spec (as such)
SMART's endpoint for next-stop predictions for a specific bus is located at `https://www.smartbus.org/DesktopModules/Smart.Endpoint/proxy.ashx?method=predictionsforbus&vid=BUSNUMBER`.
When the bus is either in storage or heading back to the terminal from its last trip, the API will return an error response which will look like this:
```
{
	"bustime-response": {
		"error": {
			"vid": "BUSNUMBER",
			"msg": "No data found for parameter"
		}
	}
}
```
When the bus is on route or heading from the terminal to its first trip, a response will look like this (it will be far longer; I've snipped all but the first three next-stop predictions):
```
{
	"bustime-response": {
		"prd": [{
			"tmstmp": "20180531 19:41",
			"typ": "A",
			"stpnm": "GRATIOT + CLINTON",
			"stpid": "22404",
			"vid": "3001",
			"dstp": "1026",
			"rt": "560",
			"rtdir": "SOUTHBOUND",
			"des": "GRATIOT to 8 MILE",
			"prdtm": "20180531 19:42",
			"tablockid": "81178",
			"tatripid": "567552",
			"zone": null
		}, {
			"tmstmp": "20180531 19:41",
			"typ": "A",
			"stpnm": "MAIN + CASS",
			"stpid": "22444",
			"vid": "3001",
			"dstp": "3855",
			"rt": "560",
			"rtdir": "SOUTHBOUND",
			"des": "GRATIOT to 8 MILE",
			"prdtm": "20180531 19:43",
			"tablockid": "81178",
			"tatripid": "567552",
			"zone": null
		}, {
			"tmstmp": "20180531 19:41",
			"typ": "A",
			"stpnm": "MAIN + PAROLE OFFICE",
			"stpid": "23494",
			"vid": "3001",
			"dstp": "4515",
			"rt": "560",
			"rtdir": "SOUTHBOUND",
			"des": "GRATIOT to 8 MILE",
			"prdtm": "20180531 19:44",
			"tablockid": "81178",
			"tatripid": "567552",
			"zone": null
		}]
	}
}
```
* *tmstmp*: timestamp of the API result
* *typ*: A for arrival or D for departure; D is only present on the first stop of a trip
* *stpnm*: Stop Name
* *stpid*: Stop ID, corresponds to textmybus and SMART's GTFS file I believe
* *dstp*: Distance remaining to the stop, in feet.
* *rt*: Route Number
* *rtdir*: Route Direction
* *des*: Description (route name; roughly corresponds to what's on the bus's headsign)
* *prdtm*: Predicted time that the bus will be at the stop in question
* *tablockid*: ?
* *tatripid*: ?
* *zone*: ? (Zoned fares aren't a thing in SMART.)
