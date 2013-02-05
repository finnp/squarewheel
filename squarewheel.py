from urllib2 import urlopen
import json
import difflib
import math
import re
from config import wheelmap_api_key
from config import foursquare_client_id
from config import foursquare_client_secret
from config import foursquare_callback_url

wheelmap_api_url = "http://wheelmap.org/api/nodes?api_key=%s" % wheelmap_api_key

foursquare_version = "&v=20130128"
foursquare_api_url = "https://api.foursquare.com/v2/"
foursquare_client_data = "?client_id=%s&client_secret=%s" % (foursquare_client_id, foursquare_client_secret)

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
        html += "<img src='/static/ajax-loader.gif' class='mapmarker' alt='Marker'/>"
        html += "</div>"
        html += "<img src='%s' alt='Map' class='img-circle'/>" % self.get_openstreetmap_image(16)
        html += "</div>"
        return html
                
class WheelmapNode:
    def __init__(self, json_node):
        self.wheelmap_id = json_node["id"]
        self.name = json_node["name"]
        self.lat = json_node["lat"]
        self.lng = json_node["lon"]
        self.wheelchair = json_node["wheelchair"]
        self.wheelchair_description = json_node["wheelchair_description"]
        self.street = json_node["street"]
        self.housenumber = json_node["housenumber"]
        self.city = json_node["city"]
        self.postcode = json_node["postcode"]
        self.website = json_node["website"]
        self.phone = json_node["phone"]
        self.node_type = json_node["node_type"]["identifier"]
        
    def get_wheelmap_node_url(self):
        return "http://wheelmap.org/nodes/%s" % self.wheelmap_id
    
    def get_wheelmap_map_url(self, zoom = 18):
        return "http://wheelmap.org/en/?lat=%s&lon=%szoom=%s" % (self.lat, self.lng, zoom)
        
    def get_openstreetmap_node_url(self):
        return "http://www.openstreetmap.org/browse/node/%s" % self.wheelmap_id
        
    def get_openstreetmap_map_url(self):
        return "http://www.openstreetmap.org/?node=%s" % self.wheelmap_id
    
    def get_color_coded_icon(self):
        return "http://wheelmap.org/marker/%s.png" % (self.wheelchair)
    
    def get_html_address(self):
        html = ""
        if self.street:
            html += self.street
            if self.housenumber:
                html += " " + self.housenumber
            html += "<br/>"
        if self.city:
            if self.postcode:
                html += self.postcode + " "
            html += self.city + "<br/>"  
        return html
    
    def get_googlemaps_image(self, width = 200, height = 200):
        uri = "http://maps.googleapis.com/maps/api/staticmap?zoom=15&size=%sx%s&sensor=false" % (width, height)
        uri += "&markers=icon:%s|%s,%s" % (self.get_color_coded_icon(), self.lat, self.lng)
        return uri
    
    def get_mapquest_image(self, zoom = 16):
        (xtile, ytile) = deg2num(self.lat, self.lng, zoom)
        uri = "http://otile3.mqcdn.com/tiles/1.0.0/osm/%s/%s/%s.jpg" % (zoom, xtile, ytile)
        return uri
    
    def get_openstreetmap_image(self, zoom = 16):
        (xtile, ytile) = deg2num(self.lat, self.lng, zoom)
        uri = "http://b.tile.openstreetmap.org/%s/%s/%s.png" % (zoom, xtile, ytile)
        return uri
    
    def get_map_with_marker(self):
        html =  "<div style='position:relative'>"
        html += "<div style='position:absolute; left:69px; top:69px;' >"
        html += "<img src='%s' alt='Marker'/>" % self.get_color_coded_icon()
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
        
def explore_foursquare(near, page = 0):
    
    per_page = 10
    
    # Form request uri
    request_uri = foursquare_api_url + "venues/explore" + foursquare_client_data + "&near=" + near
    
    request_uri += "&limit=%s&offset=%s" % (per_page, page * per_page)
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    venues = []
    
    for item in results["response"]["groups"][0]["items"]:
        venue_data = FoursquareVenue( item["venue"] )
        venues.append( venue_data )
        
    return venues
    
def get_last_foursquare_checkins(foursquare_token, page = 0):
    
    # https://developer.foursquare.com/docs/users/checkins
    # Form request uri
    request_uri = foursquare_api_url + "users/self/checkins" + foursquare_client_data + "&oauth_token=" + foursquare_token + foursquare_version
    
    per_page = 10
    
    # Number of venues limited to 10
    request_uri += "&limit=%s&offset=%s" % (per_page, page * per_page)
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    venues = []
    
    for item in results["response"]["checkins"]["items"]:
        venue_data = FoursquareVenue( item["venue"] )
        venues.append( venue_data )
    
    return venues


def get_todo_venues(foursquare_token, page = 0):
    
    request_uri = foursquare_api_url + "users/self/todos" + foursquare_client_data + "&oauth_token=" + foursquare_token + foursquare_version
    
    per_page = 10
    
    request_uri += "&sort=recent&limit=%s&offset=%s" % (per_page, page * per_page)
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    venues = []
    
    for item in results["response"]["todos"]["items"]:
        venue_data = FoursquareVenue( item["tip"]["venue"] )
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
    
    wheelmap_bbox = "&bbox=%s,%s,%s,%s" % (from_lng, from_lat, to_lng, to_lat)
    
    wheelmap_per_page = "&per_page=%s" % n
    
    # wheelmap_q = "&q=%s" % name # for /nodes/search
    
    request_uri = wheelmap_api_url + wheelmap_bbox + wheelmap_per_page
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    max_name_match = 0.0
    
    for node in results["nodes"]:
        if node["name"] and name:
            name_match = difflib.SequenceMatcher(None, node["name"], name).ratio()
            if name_match > max_name_match:
                max_node = node
                max_name_match = name_match
                
    if max_name_match > 0.6:
        return  WheelmapNode( max_node )
    else:
        return False

def get_foursquare_user(foursquare_token):
    """Takes the foursquare token for the user and returns the username and an icon as a tupel"""
    request_uri = foursquare_api_url + "users/self" + foursquare_client_data + "&oauth_token=" + foursquare_token + foursquare_version
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    user = results["response"]["user"]
    
    user["photo"]["icon"] = user["photo"]["prefix"] + "36x36" + user["photo"]["suffix"]
    
    return (user["firstName"], user["photo"]["icon"])
    
def json_node_search(name, lat, lng):
    node = search_wheelmap(lat, lng, 0.004, name, 200)
    json_response = {}
    if node:
        json_response["wheelmap"] = True 
        json_response["wheelmap_id"] = node.wheelmap_id
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
