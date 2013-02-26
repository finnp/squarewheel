# Standard libraries
import json
import difflib
import math
import re
import logging
import sys
import uuid
from urllib2 import urlopen
from urllib2 import unquote

# Third party
import foursquare 
from mongokit import Connection
from flask import session

# Local
import wheelmap
from config import FOURSQUARE_CLIENT_ID
from config import FOURSQUARE_CALLBACK_URL
from config import FOURSQUARE_CLIENT_SECRET
from config import WHEELMAP_API_KEY
from config import WHEELMAP_API_KEY_VISITOR_EDITS
from config import MONGODB_NAME
from config import MONGODB_PW
from config import MONGODB_HOST
from config import MONGODB_DBNAME
from config import MONGODB_PORT

# Add logging handler that puts everything to the console
loghandler = logging.StreamHandler(stream=sys.stdout)
foursquare.log.addHandler(loghandler)
foursquare.log.setLevel(logging.DEBUG)

class FoursquareVenue:
    __slots__ = ('foursquare_id', 'lat', 'lng', 'name', 'xtile', 'ytile')
    def __init__(self, json_venue):
        """Takes a foursquare venue from the official API"""
        self.foursquare_id = json_venue["id"]
        self.lat = json_venue["location"]["lat"]
        self.lng = json_venue["location"]["lng"]
        self.name = json_venue["name"]
        (self.xtile, self.ytile) = deg2num(self.lat, self.lng, 16)        
            
# By OpenStreetMap
def deg2num(lat_deg, lon_deg, zoom):
    """Takes latitude, longitude and zoomlevel and returns 
    the titles on openstreetmap we are looking for"""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)
           
def get_venues(foursquare_client, endpoint, page = 0, params = {}):
    per_page = 10
    params['limit'] = per_page
    params['offset'] = page * per_page
    
    if endpoint == 'todo':
        items = foursquare_client.lists('self/todos', params=params)['list']['listItems']['items']
    elif endpoint == 'lastcheckins':
        items = foursquare_client.users.checkins(params=params)['checkins']['items']
    elif endpoint == 'explore':
        items = foursquare_client.venues.explore(params=params)['groups'][0]['items'] 
    else:
        raise Exception('No endpoint')
    
    venues = []
    for item in items:
        venues.append( FoursquareVenue( item['venue'] ) )
    return venues

def search_wheelmap (lat, lng, interval, name, n):
    """Searches for a place which matches the given name in the 
    given coordinates range. Returns false if nothing found"""
    
    # Calculate the bbox for the API call
    from_lat = lat - interval
    to_lat = lat + interval
    from_lng = lng - interval
    to_lng = lng + interval
    
    # Remove parentheses (better for search, generally)
    name = re.sub(r'\([^)]*\)', '', name)
    
    wheelmap_client = wheelmap.Wheelmap(WHEELMAP_API_KEY)
    
    bbox= (from_lng, from_lat, to_lng, to_lat)
    
    nodes = wheelmap_client.nodes_collection(bbox=bbox, per_page=n)    
    
    max_name_match = 0.0
    
    for node in nodes:
        if node.name and name:
            name_match = difflib.SequenceMatcher(None, node.name, name).ratio()
            if name_match > max_name_match:
                max_node = node
                max_name_match = name_match
    
    if max_name_match > 0.6:
        return max_node
    else:
        return False

def get_foursquare_user(foursquare_client):
    """Takes the foursquare token for the user and returns the username and an icon as a tupel"""
    
    user = foursquare_client.users()["user"]
    
    user["photo"]["icon"] = user["photo"]["prefix"] + "36x36" + user["photo"]["suffix"]
    
    return (user["firstName"], user["photo"]["icon"])
    
def json_node_search(name, lat, lng):
    node = search_wheelmap(lat, lng, 0.004, name, 200)
    json_response = {}
    if node:
        json_response["wheelmap"] = True 
        json_response["wheelmapId"] = node.node_id
        json_response["name"] = node.name
        json_response["lat"] = node.lat
        json_response["lng"] = node.lng
        json_response["wheelchair"] = node.wheelchair 
        json_response["wheelchairDescription"] = node.wheelchair_description
        #json_response["street"] = node.street
        #json_response["housenumber"] = node.housenumber
        #json_response["city"] = node.city
        #json_response["postcode"] = node.postcode
        json_response["website"] = node.website
        json_response["phone"] = node.phone 
        json_response["nodeType"] = node.node_type
        json_response["address"] = node.get_html_address()
    else: 
        json_response["wheelmap"] = False
    return json.dumps(json_response, indent=4, separators=(',', ': '))
    
def update_wheelchair_status(node_id, wheelchair_status):
    wheelmap_client = wheelmap.Wheelmap(WHEELMAP_API_KEY_VISITOR_EDITS if WHEELMAP_API_KEY_VISITOR_EDITS else WHEELMAP_API_KEY) 
    return wheelmap_client.nodes_update_wheelchair(node_id=node_id, wheelchair=wheelchair_status)
    
def mongodb_get_users():
    """Connects to mongodb and returns users collection"""
    
    connection = Connection(MONGODB_HOST, MONGODB_PORT)
    if MONGODB_NAME and MONGODB_PW:
        connection[MONGODB_DBNAME].authenticate(MONGODB_NAME, MONGODB_PW)    
    return connection[MONGODB_DBNAME].users

    
def get_foursquare_client():
    """Returns a tupel (user_logged_in, foursquare client)"""
        
    if 'session_key' in session:
        collection = mongodb_get_users()
        user = collection.find_one({'session_key': unicode(session['session_key']) })
        if user:
            return (True, foursquare.Foursquare(access_token=user['access_token'], version="20130128"))
    return (False, foursquare.Foursquare(client_id=FOURSQUARE_CLIENT_ID, client_secret=FOURSQUARE_CLIENT_SECRET, redirect_uri=FOURSQUARE_CALLBACK_URL, version="20130128"))
   
def foursquare_add_comment(foursquare_client, venueId, text, url):
    
    params = {'text': text, 'venueId': venueId}
    if url:
        params['url'] = url
            
    foursquare_client.tips.add(params=params)
    
    return True

    
def user_login(access_token, foursquare_id):
    """Logs in the user and returns a session_key"""
    
    # Get the collection of users from mongodb
    users = mongodb_get_users()
    
    # Generate the session key
    session_key = uuid.uuid1()
    
    data = {'$set': {'session_key': unicode(session_key), 'access_token': unicode(access_token) } }
    users.update({'_id': unicode(foursquare_id)}, data, upsert = True)
    
    return session_key

def user_disconnect():    
    users = mongodb_get_users()
    to_delete = users.find_one({'session_key': unicode(session['session_key'])})
    users.remove(to_delete) 
    session.pop('session_key', None)
    
    
