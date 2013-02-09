from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import g
from urllib2 import urlopen
import os
import json
import squarewheel
import foursquare
import uuid
from mongokit import Connection
from config import FOURSQUARE_CLIENT_ID
from config import FOURSQUARE_CALLBACK_URL
from config import FOURSQUARE_CLIENT_SECRET
from config import FLASK_SECRET_KEY


# MongoDB configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

app = Flask(__name__)
app.config.from_object(__name__)
connection = Connection(app.config['MONGODB_HOST'],
                        app.config['MONGODB_PORT'])
                            


@app.before_request
def before_request():
    
    if 'session_key' in session:
        g.foursquare_enabled = True
        collection = connection["dbname"].users
        user = collection.find_one({'session_key': unicode(session['session_key']) })
        if user:
            g.foursquare_client = foursquare.Foursquare(access_token=user['access_token'], version="20130128")
            (g.foursquare_firstname, g.foursquare_icon) = squarewheel.get_foursquare_user(g.foursquare_client)
        else:
            g.foursquare_enabled = False
    else:
        g.foursquare_enabled = False
        g.foursquare_client = foursquare.Foursquare(client_id=FOURSQUARE_CLIENT_ID, client_secret=FOURSQUARE_CLIENT_SECRET, redirect_uri=FOURSQUARE_CALLBACK_URL, version="20130128")
    
        
@app.route('/')
def startpage():
    foursquare_oauth_url = g.foursquare_client.oauth.auth_url()
    return render_template('start.html', foursquare_oauth_url = foursquare_oauth_url)

@app.route('/foursquare/venues/explore/<city>', defaults={'page': 0})
@app.route('/foursquare/venues/explore/<city>/<int:page>')
def explore_city(city, page):
    venues = squarewheel.explore_foursquare(g.foursquare_client, city, page)
    return render_template('venue_list.html', venues=venues)

@app.route('/foursquare/venues/lastcheckins', defaults={'page': 0})
@app.route('/foursquare/venues/lastcheckins/<int:page>')
def lastcheckins(page):
    # Change this and comminicate with Javascript
       
    venues = squarewheel.get_last_foursquare_checkins(g.foursquare_client, page)
    return render_template('venue_list.html', venues=venues)
    
@app.route('/foursquare/venues/todo', defaults={'page': 0})
@app.route('/foursquare/venues/todo/<int:page>')
def todo(page):
    
    venues = squarewheel.get_todo_venues(g.foursquare_client, page)
    return render_template('venue_list.html', venues=venues)
    
@app.route('/wheelmap/nodes')
def get_nodes():
    lat = request.args.get('lat', '', type=float)
    lng = request.args.get('lng', '', type=float)
    name = request.args.get('name', '')
    return squarewheel.json_node_search(name, lat, lng)
        
        
@app.route('/foursquare')
def foursquare_callback():
    
   
    code = request.args.get('code', '')
    access_token = g.foursquare_client.oauth.get_token(code)
    g.foursquare_client.set_access_token(access_token)
    
    # <MongoDB>
    session_key = uuid.uuid1()
    session['session_key'] = session_key
    collection = connection["dbname"].users
    user = {'session_key': unicode(session_key), 'access_token': unicode(access_token) }
    collection.insert(user)    
    # </MongoDB>
    
    (g.foursquare_firstname, g.foursquare_icon) = squarewheel.get_foursquare_user(g.foursquare_client)
    g.foursquare_enabled = True
    return render_template('start.html')

@app.route('/disconnect')
def foursquare_disconnect():
    session.clear()
    session.pop('foursquare_token', None)
    session.pop('foursquare_icon', None)
    session.pop('foursquare_enabled', None)
    return "Session cleared"

@app.route('/wheelmap/update_node/<node_id>/<wheelchair_status>')
def wheelmap_update_node(node_id, wheelchair_status):
    # Works but maybe change it, so that it to POST/PUT, so it can not so easily
    # be used to change nodes through the url
    if squarewheel.update_wheelchair_status(node_id, wheelchair_status):
        return "Successfull"
    else:
        return "Failed."
        

app.secret_key = FLASK_SECRET_KEY

if __name__ == '__main__':
    app.debug = True
    #app.debug = False
    if app.debug:
        app.run()
    else:
        # Bind to PORT if defined, otherwise default to 5000.
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    
