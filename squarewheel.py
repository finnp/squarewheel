from urllib2 import urlopen
import json
import difflib
import math
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
        
def explore_foursquare(near):
    
    # Form request uri
    request_uri = foursquare_api_url + "venues/explore" + foursquare_client_data + "&near=" + near
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    venues = []
    
    for item in results["response"]["groups"][0]["items"]:
        venue_data = FoursquareVenue( item["venue"] )
        venues.append( venue_data )
        
    return venues
    
def get_last_foursquare_checkins(foursquare_token):
    
    # https://developer.foursquare.com/docs/users/checkins
    # Form request uri
    request_uri = foursquare_api_url + "users/self/checkins" + foursquare_client_data + "&oauth_token=" + foursquare_token + foursquare_version
    
    # Number of venues limited to 50
    request_uri += "&limit=50"
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    venues = []
    
    for item in results["response"]["checkins"]["items"]:
        venue_data = FoursquareVenue( item["venue"] )
        venues.append( venue_data )
        
    return venues


def search_wheelmap (lat, lng, interval, name):
    """Searches for a place which matches the given name in the 
    given coordinates range. Returns false if nothing found"""
    
    # Calculate the bbox for the API call
    from_lat = lat - interval
    to_lat = lat + interval
    from_lng = lng - interval
    to_lng = lng + interval
    
    wheelmap_bbox = "&bbox=%s,%s,%s,%s" % (from_lng, from_lat, to_lng, to_lat)
    
    wheelmap_per_page = "&per_page=100"
    
    # wheelmap_q = "&q=%s" % name # for /nodes/search
    
    request_uri = wheelmap_api_url + wheelmap_bbox + wheelmap_per_page
    
    if printstatus:
        print "Opening %s" % request_uri
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    # Basically check nearest
    #if len(results["nodes"]) > 1:
    #    for node in results["nodes"]:
    #        if node["name"] == name:
    #            return WheelmapNode(node)
    #    return False
    #elif len(results["nodes"]) == 1:
    #    return WheelmapNode( results["nodes"][0] )
    #else:
    #    return False
        
    for node in results["nodes"]:
        if node["name"] and name:
            name_match = difflib.SequenceMatcher(None, node["name"], name).ratio()
            if name_match > 0.8:
                return WheelmapNode( node )
    return False

def get_foursquare_user(foursquare_token):
    """Takes the foursquare token for the user and returns the username and an icon as a tupel"""
    request_uri = foursquare_api_url + "users/self" + foursquare_client_data + "&oauth_token=" + foursquare_token + foursquare_version
    
    response = urlopen(request_uri).read()
    
    results = json.loads(response)
    
    user = results["response"]["user"]
    
    user["photo"]["icon"] = user["photo"]["prefix"] + "36x36" + user["photo"]["suffix"]
    
    return (user["firstName"], user["photo"]["icon"])
    
def add_nodes_to_venues(venues):
    for venue in venues:
        node = search_wheelmap(venue.lat, venue.lng, 0.0004, venue.name) 
        if node:
            venue.wheelmap_node = node
    return venues
    

#venues_in_hamburg = explore_foursquare("Hamburg")

#for venue in venues_in_hamburg:
#    node = search_wheelmap(venue.lat, venue.lng, 0.0003, venue.name)
#    if node:
#        print node.name, "-for-", venue.name
