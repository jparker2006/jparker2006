#!/usr/bin/env python3
"""Refresh data/contributions.json from GitHub's contribution calendar (GraphQL).

    GITHUB_TOKEN=... python3 generator/fetch.py jparker2006 data/contributions.json

Run in GitHub Actions with the workflow's GITHUB_TOKEN, which sees what the public sees. Fetches the last
twelve calendar months and merges them into the stored history. Standard library only.
"""
import datetime, json, os, sys, urllib.request

login, path = sys.argv[1], sys.argv[2]
today = datetime.datetime.now(datetime.timezone.utc).date()
start = datetime.date(today.year - (1 if today.month < 12 else 0), (today.month % 12) + 1, 1)   # first day, 11 months back
query = '''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){
  contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
body = json.dumps({'query': query, 'variables': {'login': login, 'from': f'{start}T00:00:00Z', 'to': f'{today}T23:59:59Z'}}).encode()
req = urllib.request.Request('https://api.github.com/graphql', body, {
    'Authorization': f'bearer {os.environ["GITHUB_TOKEN"]}', 'Content-Type': 'application/json', 'User-Agent': 'profile-art'})
res = json.load(urllib.request.urlopen(req, timeout=30))
if 'errors' in res: sys.exit(f'GraphQL error: {res["errors"]}')
weeks = res['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
fresh = {d['date']: d['contributionCount'] for w in weeks for d in w['contributionDays'] if d['date'] <= str(today)}
store = json.load(open(path)) if os.path.exists(path) else {'days': []}
days = dict(store['days']); days.update(fresh)
store.update(source='GitHub GraphQL contributionCalendar (public view)', fetched=str(today), days=sorted(days.items()))
json.dump(store, open(path, 'w'))
print(f'{len(fresh)} days fetched ({start} .. {today}), {len(days)} stored')
