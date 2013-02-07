import requests

WHEELMAP_API_URL = "http://wheelmap.org/api/" 

class Wheelmap:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def request(self, endpoint, method, params={}):
        """General function for all requests."""
        params["api_key"] = self.api_key
        endpoint_url = WHEELMAP_API_URL + endpoint
        r = requests.request(method, endpoint_url, params=params)
        return r.json()
    
    def nodes_collection(self, bbox=None, wheelchair=None, page=None, per_page=None):
        """Function for /api/nodes?bbox&wheelchair&page&per_page
        It returns a list of WheelmapNodes"""
        params={}
        
        if type(bbox) == str:
            params["bbox"] = bbox
        elif type(bbox) == tuple:
            params["bbox"] = "{},{},{},{}".format(*bbox)
        
        if wheelchair:
            params["wheelchair"] = wheelchair
        
        if page:
            params["page"] = page
        
        if per_page:
            params["per_page"] = per_page
        
        r = self.request("nodes", "GET", params)

        if "nodes" in r:
            nodes = []
            for node in r["nodes"]:
                nodes.append(WheelmapNode(node))
        
        return nodes
    
    def nodes_update_wheelchair(self, node=None, node_id=None, wheelchair=None):
        """/api/nodes/{node_id}/update_wheelchair"""
        
        if node:
            endpoint = "nodes/{}/update_wheelchair".format(node.node_id)
        else:
            endpoint = "nodes/{}/update_wheelchair".format(node_id)
        
        params = {'wheelchair': wheelchair}
        
        r = self.request(endpoint, "PUT", params=params)
                      
        if "message" in r:
            return True
        else:
            return False
                

class WheelmapNode:
    def __init__(self, json_node):
        # id is node_id, because of python inbuild .id()
        self.node_id = json_node["id"]
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
