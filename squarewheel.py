from urllib2 import urlopen
import json
import difflib
import math
import re
import wheelmap
from config import WHEELMAP_API_KEY

printstatus = False

class FoursquareVenue:
    def __init__(self, json_venue):
        self.foursquare_id = json_venue["id"]
        self.lat = json_venue["location"]["lat"]
        self.lng = json_venue["location"]["lng"]
        self.name = json_venue["name"]
        self.wheelmap_node = None
    
    def get_foursquare_venue_url(self):
        return "https://foursquare.com/v/%s" % self.foursquare_id
        
    def get_openstreetmap_image(self, zoom = 16):
        (xtile, ytile) = deg2num(self.lat, self.lng, zoom)
        uri = "http://b.tile.openstreetmap.org/%s/%s/%s.png" % (zoom, xtile, ytile)
        return uri
    
    def get_map_with_marker(self):
        html =  "<div style='position:relative'>"
        html += "<div style='position:absolute; left:69px; top:69px;' >"
        html += "<img src='/static/img/ajax-loader.gif' class='mapmarker' alt='Marker'/>"
        html += "</div>"
        html += "<img src='%s' alt='Map' class='img-circle'/>" % self.get_openstreetmap_image(16)
        html += "</div>"
        return html
        
            
# By OpenStreetMap
def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)
        
def explore_foursquare(foursquare_client, near, page = 0):
    
    per_page = 10
    
    params = {'limit': per_page, 'offset': page * per_page, 'near': near}
    
    results = foursquare_client.venues.explore(params=params)
    
    venues = []
    
    for item in results["groups"][0]["items"]:
        venue_data = FoursquareVenue( item["venue"] )
        venues.append( venue_data )
        
    return venues
    
def get_last_foursquare_checkins(foursquare_client, page = 0):
    
    per_page = 10
    
    params = {'limit': per_page, 'offset': page * per_page}
    
    results = foursquare_client.users.checkins(params=params)
    
    venues = []
    
    for item in results["checkins"]["items"]:
        venue_data = FoursquareVenue( item["venue"] )
        venues.append( venue_data )
    
    return venues


def get_todo_venues(foursquare_client, page = 0):
    
    per_page = 10
    
    params = {'limit': per_page, 'offset': page * per_page}
    
    results = foursquare_client.lists("self/todos", params=params)
    
    venues = []
    
    for item in results["list"]["listItems"]["items"]:
        venue_data = FoursquareVenue( item["venue"] )
        venues.append( venue_data )
        
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
        json_response["wheelmap_id"] = node.node_id
        json_response["name"] = node.name
        json_response["lat"] = node.lat
        json_response["lng"] = node.lng
        json_response["wheelchair"] = node.wheelchair 
        json_response["wheelchair_description"] = node.wheelchair_description
        json_response["street"] = node.street
        json_response["housenumber"] = node.housenumber
        json_response["city"] = node.city
        json_response["postcode"] = node.postcode
        json_response["website"] = node.website
        json_response["phone"] = node.phone 
        json_response["node_type"] = node.node_type
    else: 
        json_response["wheelmap"] = False
    return json.dumps(json_response, indent=4, separators=(',', ': '))
    
def update_wheelchair_status(node_id, wheelchair_status):
    wheelmap_client = wheelmap.Wheelmap(WHEELMAP_API_KEY)
    return wheelmap_client.nodes_update_wheelchair(node_id=node_id, wheelchair=wheelchair_status)
    
