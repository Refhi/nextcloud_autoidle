#!/usr/bin/env python3
## check calendar specified in user.json for specific entry
## change status depending of said entry

import time
from datetime import date  # caldav required
from datetime import datetime, timedelta
import json
import requests 
import caldav

## define surveillance frequency (in seconds)
frequency = 60

## important basic urls
base_url = "example.com"
caldav_url = f"https://{base_url}/remote.php/dav/calendars/"
api_url = f"https://{base_url}/ocs/v2.php/apps/user_status/api/v1/user_status"

# check/define possible status allowed by nextcloud API
online = "online"
away = "away"
dnd = "dnd"
invisible = "invisible"
offline = "offline"

actions = {
    "Défault": dnd,
    "Pause": away,
    "invisible": invisible,
    "Travail": online,
    "Vacances": dnd,
    "Off": dnd,
}

# import user dictionnary from users.json
with open("users.json") as f:
    dict_users = json.load(f)

class Users:
    def __init__(self, user, calendar, status, password):
        self.user = user
        self.calendar = calendar
        self.status = status
        self.password = password

    def __str__(self):  # print info (for debug, not currently used)
        print = f"je suis l'instance {self.user} avec le calendrier {self.calendar} et le status {self.status}"
        return print

    def getcalendar(self): # return a status depending on calendar entry
        print(f"on me demande de récupérer entrées du calendrier de {self.user}")
        client = caldav.DAVClient(
            url=caldav_url,
            username=self.user,
            password=self.password,
        )
        my_principal = client.principal()
        my_new_calendar = my_principal.calendar(name=self.calendar)
        events_fetched = my_new_calendar.search(
            start=datetime.now(),
            end=(datetime.now() + timedelta(seconds=30)),
            event=True,
            expand=True,
        )
        eventslist = []
        self.statuslist = []
        j = 0
        for i in events_fetched:
            data = events_fetched[j].data.splitlines()[5][8:]
            eventslist.append(data)
            j = j + 1
            if data in actions:
                self.statuslist.append(actions[data])
        print(f"les évènements sont {eventslist} et les status sont {self.statuslist}")
        if len(self.statuslist) == 0:
            self.statuslist = ["dnd"]
        # if there are multiple entry at the same time, it priorise the asked status
        # depending on the order of the "actions" dictionnary
        elif len(self.statuslist) >= 2:
            print("plus d'un status demandé, je priorise :")
            for key, item in actions.items():
                print(f"je teste {item}")
                if item in self.statuslist:
                    print(f"trouvé {item} dans les status demandés, je le priorise")
                    self.statuslist = [item]
                    break
        return self.statuslist  # la valeur lisible par l'API

    def setstatus(self, askedstatus):
        print(f"on me demande de mettre en place le status {askedstatus}")
        url = f"{api_url}/status"
        response = requests.put(
            url,
            auth=(self.user, self.password),
            headers={"OCS-APIRequest": "true", "Accept": "application/json"},
            data={"statusType": askedstatus},
        )
        print(f"status demandé : le retour de l'API est : {response.text}")

    def getstatus(self):
        response = requests.get(
            api_url,
            auth=(self.user, self.password),
            headers={
                "OCS-APIRequest": "true",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response = response.json()
        self.statusdic = response["ocs"]["data"]
        return self.statusdic


# instances init :
person = {}
for user, values in dict_users.items():
    calendar = values["calendar"]
    status = values["status"]
    password = values["password"]
    person[user] = Users(user, calendar, status, password)
    # print(person[user])


## main
while True:
    for user in dict_users:
        # get actual user status as a dictionnary
        statusdic = person[user].getstatus()
        icon = person[user].statusdic["icon"]
        status = person[user].statusdic["status"]
        print(f"je travaille sur {user}, d'icone {icon} et de status {status}")
        try:
            askedstatus = person[user].getcalendar()
        except:
            calendar = person[user].calendar
            print(f'calendrier "{calendar}" non trouvé pour "{user}"')
            askedstatus = "dnd"
            print(f"on demande le(s) status : {askedstatus}")

        if askedstatus != [status]:
            person[user].setstatus(askedstatus)
        else:
            print("status à jour")
    time.sleep(frequency)
