import os
import requests
import arrow
from icalendar import Calendar, Event
from datetime import timedelta

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
    
    # Check if user wants full history
    sync_full = os.environ.get('SYNC_FULL_HISTORY', 'false').lower() == 'true'
    
    all_activities = []
    page = 1
    per_page = 200 if sync_full else 50 # Max default 30, but can go up to 200
    
    while True:
        print(f"Fetching page {page}...")
        res = requests.get(
            f"https://www.strava.com/api/v3/athlete/activities?per_page={per_page}&page={page}", 
            headers=headers
        )
        res.raise_for_status()
        data = res.json()
        
        if not data:
            break
            
        all_activities.extend(data)
        
        if not sync_full:
            break
            
        page += 1
        
    print(f"Total activities fetched: {len(all_activities)}")
    return all_activities

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
    c.add('prodid', '-//Strava Calendar//EN')
    c.add('version', '2.0')
    for act in activities:
        e = Event()
        if act['type'] == 'Run':
            emoji = "🏃"
        elif act['type'] == 'Ride':
            emoji = "🚴"
        elif act['type'] == 'Walk':
            emoji = "🚶"
        else:
            emoji = "🏅"

        e.add('summary', f"{emoji} {act['name']}")
        start_dt = arrow.get(act['start_date']).datetime
        e.add('dtstart', start_dt)
        e.add('dtend', start_dt + timedelta(seconds=act['moving_time']))

        dist_km = act['distance'] / 1000
        description = f"Distance: {dist_km:.2f} km"

        if act.get('average_heartrate'):
            description += f"\nHeart Rate: {int(act['average_heartrate'])} bpm"

        description += f"\nLink: https://www.strava.com/activities/{act['id']}"
        e.add('description', description)
        c.add_component(e)

    return c.to_ical().decode('utf-8')

if __name__ == "__main__":
    token = get_access_token()
    acts = get_activities(token)
    ics_content = create_ics_content(acts)
    update_gist(ics_content)