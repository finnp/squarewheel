from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import g
from flask import jsonify
from urllib2 import urlopen
import os
import json
import squarewheel
import foursquare
import uuid
import logging
from mongokit import Connection
#from config import FOURSQUARE_CLIENT_ID
#from config import FOURSQUARE_CALLBACK_URL
#from config import FOURSQUARE_CLIENT_SECRET
from config import FLASK_SECRET_KEY
from config import MONGODB_HOST
from config import MONGODB_PORT
from config import MONGODB_DBNAME
from config import MONGODB_NAME
from config import MONGODB_PW

app = Flask(__name__)
app.config.from_object(__name__)
       
@app.route('/')
def startpage():
    if not request.is_xhr:
        fq_logged_in, foursquare_client = squarewheel.get_foursquare_client(session)
        if fq_logged_in:
            foursquare_firstname, foursquare_icon = squarewheel.get_foursquare_user(foursquare_client)
            foursquare_oauth_url = False
        else:
            foursquare_oauth_url = foursquare_client.oauth.auth_url()
            foursquare_firstname = False
            foursquare_icon = False
    else:
        foursquare_oauth_url = False
        foursquare_firstname = False
        foursquare_icon = False
    return render_template('start.html', foursquare_oauth_url = foursquare_oauth_url, foursquare_icon=foursquare_icon, foursquare_firstname=foursquare_firstname)

@app.route('/foursquare/venues/explore/<city>', defaults={'page': 0})
@app.route('/foursquare/venues/explore/<city>/<int:page>')
def explore_city(city, page):
    foursquare_client = squarewheel.get_foursquare_client(session)[1]
    try:
        venues = squarewheel.explore_foursquare(foursquare_client, city, page)
    except foursquare.FailedGeocode, e:
        return "Foursquare could not find the location"
    else:
        return render_template('venue_list.html', venues=venues)


        
@app.route('/foursquare/venues/lastcheckins', defaults={'page': 0})
@app.route('/foursquare/venues/lastcheckins/<int:page>')
def lastcheckins(page):
    (fq_logged_in, foursquare_client) = squarewheel.get_foursquare_client(session)
    if fq_logged_in:
        venues = squarewheel.get_last_foursquare_checkins(foursquare_client, page)
        return render_template('venue_list.html', venues=venues)
    else:
        return "Not connected to foursquare."
    
@app.route('/foursquare/venues/todo', defaults={'page': 0})
@app.route('/foursquare/venues/todo/<int:page>')
def todo(page):
    (fq_logged_in, foursquare_client) = squarewheel.get_foursquare_client(session)
    if fq_logged_in:
        venues = squarewheel.get_todo_venues(foursquare_client, page)
        return render_template('venue_list.html', venues=venues)
    else:
        return "Not connected to foursquare."
    
@app.route('/wheelmap/nodes')
def get_nodes():
    lat = request.args.get('lat', '', type=float)
    lng = request.args.get('lng', '', type=float)
    name = request.args.get('name', '')
    return squarewheel.json_node_search(name, lat, lng)
        
        
@app.route('/foursquare')
def foursquare_callback():
    
    (fq_logged_in, foursquare_client) = squarewheel.get_foursquare_client(session)
    
    if not fq_logged_in:
    
        code = request.args.get('code', '')
        
        print "Code received: %s" % code
        
        access_token = foursquare_client.oauth.get_token(code)
        
        print "Access Token received: %s" % access_token
        
        foursquare_client.set_access_token(access_token)
        
        print "Access token set."
        
        connection = Connection(MONGODB_HOST, MONGODB_PORT)
        
        # <MongoDB>
        session_key = uuid.uuid1()
        session['session_key'] = session_key
        collection = connection[MONGODB_DBNAME].users
        user = {'session_key': unicode(session_key), 'access_token': unicode(access_token) }
        collection.insert(user)    
        # </MongoDB>
           
        foursquare_firstname, foursquare_icon = squarewheel.get_foursquare_user(foursquare_client)
        return render_template('start.html', foursquare_firstname=foursquare_firstname, foursquare_icon=foursquare_icon)
    else:
        return "Already logged in"

@app.route('/disconnect')
def foursquare_disconnect():
    session.pop('session_key', None)
    return "Session cleared"

@app.route('/wheelmap/update_node/', methods=['POST'])
def wheelmap_update_node():
    # Works but maybe change it, so that it to POST/PUT, so it can not so easily
    # be used to change nodes through the url
    if request.is_xhr:
        if squarewheel.update_wheelchair_status(request.form['wheelmapid'],
                                                request.form['wheelchairstatus']):
            return jsonify(success=True)
        else:
            abort(400)
        

app.secret_key = FLASK_SECRET_KEY


if __name__ == '__main__':
    app.debug = True 
    #app.debug = False
    if app.debug: #exception
        app.run()
    else:
        # Bind to PORT if defined, otherwise default to 5000.
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    
