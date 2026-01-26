import os
import requests
import arrow
from ics import Calendar, Event

# Secrets
CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('STRAVA_REFRESH_TOKEN')
# Nouveaux secrets pour le Gist
GIST_TOKEN = os.environ.get('GIST_TOKEN')
GIST_ID = os.environ.get('GIST_ID')

def get_access_token():
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    res = requests.post("https://www.strava.com/oauth/token", data=payload)
    res.raise_for_status()
    return res.json()['access_token']

def get_activities(token):
    headers = {'Authorization': f"Bearer {token}"}
    res = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=50", headers=headers)
    res.raise_for_status()
    return res.json()

def update_gist(content):
    """Envoie le contenu vers le Gist Secret"""
    print("Mise à jour du Gist Secret...")
    headers = {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "files": {
            "strava.ics": {
                "content": content
            }
        }
    }
    res = requests.patch(f"https://api.github.com/gists/{GIST_ID}", json=payload, headers=headers)
    res.raise_for_status()
    print("Gist mis à jour !")

def create_ics_content(activities):
    c = Calendar()
    for act in activities:
        e = Event()
        emoji = "🏃" if act['type'] == 'Run' else "🚴" if act['type'] == 'Ride' else "🏅"
        e.name = f"{emoji} {act['name']}"
        e.begin = arrow.get(act['start_date']).datetime
        e.duration = {"seconds": act['moving_time']}
        dist_km = act['distance'] / 1000
        e.description = f"Distance: {dist_km:.2f} km\nLink: https://www.strava.com/activities/{act['id']}"
        c.events.add(e)
    
    # Retourne le texte du calendrier au lieu de créer un fichier
    return c.serialize()

if __name__ == "__main__":
    token = get_access_token()
    acts = get_activities(token)
    ics_content = create_ics_content(acts)
    update_gist(ics_content)