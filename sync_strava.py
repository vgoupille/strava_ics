import requests
import arrow
from ics import Calendar, Event
import os

# Vos secrets seront injectés via les variables d'environnement GitHub
CLIENT_ID = os.environ['STRAVA_CLIENT_ID']
CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
REFRESH_TOKEN = os.environ['STRAVA_REFRESH_TOKEN']

def get_access_token():
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    res = requests.post("https://www.strava.com/oauth/token", data=payload)
    return res.json()['access_token']

def get_activities(token):
    headers = {'Authorization': f"Bearer {token}"}
    # On récupère les 30 dernières activités
    res = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=30", headers=headers)
    return res.json()

def create_ics(activities):
    c = Calendar()
    for act in activities:
        e = Event()
        e.name = f"{act['type']} : {act['name']}"
        e.begin = act['start_date'] # Format ISO géré par arrow/ics
        e.duration = {"seconds": act['moving_time']}
        e.description = f"Distance: {act['distance']/1000:.2f}km\nDénivelé: {act['total_elevation_gain']}m"
        c.events.add(e)
    
    with open('strava.ics', 'w') as f:
        f.writelines(c.serialize_iter())

if __name__ == "__main__":
    token = get_access_token()
    activities = get_activities(token)
    create_ics(activities)
    print("Calendrier mis à jour !")