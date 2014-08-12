import json
import math
import re
import sys
import uuid
from urllib2 import urlopen
from urllib2 import unquote
from difflib import SequenceMatcher
from os import environ as env

from mongokit import Connection
from flask import session

import wheelmap
import simple4sq as fq

fq.cred = (env['FOURSQUARE_CLIENT_ID'], env['FOURSQUARE_CLIENT_SECRET'], env['FOURSQUARE_CALLBACK_URL'])

class FoursquareVenue:
    """Class for transporting information about the venue. Includes
    the identifier for the tiles used from openstreetmap."""
    __slots__ = ('foursquare_id', 'lat', 'lng', 'name', 'xtile', 'ytile')
    def __init__(self, json_venue):
        """Takes a foursquare venue from the official API"""
        self.foursquare_id = json_venue['id']
        self.lat = json_venue['location']['lat']
        self.lng = json_venue['location']['lng']
        self.name = json_venue['name']
        (self.xtile, self.ytile) = osm_deg2num(self.lat, self.lng, 16)        
            
def osm_deg2num(lat_deg, lon_deg, zoom):
    """Takes latitude, longitude and zoomlevel and returns 
    the titles on openstreetmap we are looking for"""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)
           
def get_venues(endpoint, page = 0, params = {}):
    """Takes an endpoint and requests venues from foursquare"""
    per_page = 10
    params['limit'] = per_page
    params['offset'] = page * per_page
    
    fq_r = fq.request(endpoint,params=params)
    
    if endpoint == 'lists/self/todos':
        items = fq_r['list']['listItems']['items']
    elif endpoint == 'users/self/checkins':
        items = fq_r['checkins']['items']
    elif endpoint == 'venues/explore':
        items = fq_r['groups'][0]['items'] 
    else:
        raise Exception('This endpoint does not exist.')
    
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
    
    wheelmap_client = wheelmap.Wheelmap(env['WHEELMAP_API_KEY'])
    
    bbox= (from_lng, from_lat, to_lng, to_lat)
    
    nodes = wheelmap_client.nodes_collection(bbox=bbox, per_page=n)    
    
    # max_node and max_name_match are holding the
    # best match through the SequenceMatcher after the loop    
    max_name_match = 0.0
    
    for node in nodes:
        if node.name and name:
            name_match = SequenceMatcher(None, node.name, name).ratio()
            if name_match > max_name_match:
                max_node = node
                max_name_match = name_match
                
    # Is the best match better than 60% ?
    # If yes, let's take it. Otherwise nothing was found.
    if max_name_match > 0.6:
        return max_node
    else:
        return False

def get_fq_user():
    """Takes the foursquare token for the user and returns the username and an icon as a tupel"""
    user = fq.request('users/self')['user']
    user_icon = user['photo']['prefix'] + '36x36' + user['photo']['suffix']
    return (user['firstName'], user_icon)
    
def json_node_search(name, lat, lng):
    """Searches for a node near lat lng and returns a json
    response of a found node"""
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
    wheelmap_client = wheelmap.Wheelmap(env['WHEELMAP_API_KEY_VISITOR_EDITS'] if 'WHEELMAP_API_KEY_VISITOR_EDITS' in env else env['WHEELMAP_API_KEY']) 
    return wheelmap_client.nodes_update_wheelchair(node_id=node_id, wheelchair=wheelchair_status)
    
def mongodb_get_users():
    """Connects to mongodb and returns users collection"""
    # TODO parse: MONGOHQ_URL
    
    connection = Connection(env['MONGODB_HOST'], int(env['MONGODB_PORT']))
    if 'MONGODB_NAME' in env and 'MONGODB_PW' in env:
        connection[env['MONGODB_DBNAME']].authenticate(env['MONGODB_NAME'], env['MONGODB_PW'])
    return connection[env['MONGODB_DBNAME']].users

    
def fq_logged_in():
    """Returns true if the user is logged in"""
        
    if 'session_key' in session:
        collection = mongodb_get_users()
        user = collection.find_one({'session_key': unicode(session['session_key']) })
        if user:
            fq.access_token = user['access_token']
            return True
    return False

def fq_add_comment(venueId, text, url):
    
    params = {'text': text, 'venueId': venueId}
    if url:
        params['url'] = url
            
    fq.request('tips/add',params=params,method='POST')
    
    return True

    
def user_login(code):
    """Logs in the user and returns a session_key"""
    
    # Get the collection of users from mongodb
    users = mongodb_get_users()
    
    # Generate the session key
    session_key = uuid.uuid1()
    
    # Set the access_token       
    fq.download_token(code)                   
    
    data = {'$set': {'session_key': unicode(session_key), 'access_token': unicode(fq.access_token) } }
    
    foursquare_id = fq.request('users/self')['user']['id']
    
    users.update({'_id': unicode(foursquare_id)}, data, upsert = True)
    
    return session_key

def user_disconnect():    
    if 'session_key' in session:
        users = mongodb_get_users()
        to_delete = users.find_one({'session_key': unicode(session['session_key'])})
        users.remove(to_delete) 
        session.pop('session_key', None)
    if fq.access_token:
        fq.access_token = False
   
    
    
