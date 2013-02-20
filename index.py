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
from config import DEBUG

app = Flask(__name__)
app.config.from_object(__name__)
       
@app.route('/')
def startpage():
    foursquare.AUTH_ENDPOINT = 'https://foursquare.com/oauth2/authorize'
    
    disconnect = request.args.get('disconnect', '', type=bool)
    if disconnect:
        connection = Connection(MONGODB_HOST, MONGODB_PORT)
        if MONGODB_NAME and MONGODB_PW:
            connection[MONGODB_DBNAME].authenticate(MONGODB_NAME, MONGODB_PW)
        collection = connection[MONGODB_DBNAME].users
        to_delete = collection.find_one({'session_key': unicode(session['session_key'])})
        collection.remove(to_delete) 
        # </MongoDB>
        session.pop('session_key', None)

    
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

@app.route('/explore/')
def explore_city():
    
    geolocation = request.args.get('geolocation', '')
    query = request.args.get('query', '')
    page = request.args.get('page', '', type=int)
    
    (fq_logged_in, foursquare_client) = squarewheel.get_foursquare_client(session)
    try:
        venues = squarewheel.explore_foursquare(foursquare_client, geolocation, page, query)
    except foursquare.FailedGeocode, e:
        return "Foursquare could not find the location", 404
    else:
        return render_template('venue_list.html', venues=venues, fq_logged_in = fq_logged_in)


        
@app.route('/lastcheckins/')
def lastcheckins():
    page = request.args.get('page', '', type=int)
    
    (fq_logged_in, foursquare_client) = squarewheel.get_foursquare_client(session)
    if fq_logged_in:
        venues = squarewheel.get_last_foursquare_checkins(foursquare_client, page)
        return render_template('venue_list.html', venues=venues, fq_logged_in = True)
    else:
        return "You have to be connected to foursquare to use this.", 412
    
@app.route('/todo/')
def todo():
    page = request.args.get('page', '', type=int)
    (fq_logged_in, foursquare_client) = squarewheel.get_foursquare_client(session)
    if fq_logged_in:
        venues = squarewheel.get_todo_venues(foursquare_client, page)
        return render_template('venue_list.html', venues=venues, fq_logged_in = True)
    else:
        return "You have to be connected to foursquare to use this.", 412
    
@app.route('/wheelmap/nodes')
def get_nodes():
    lat = request.args.get('lat', '', type=float)
    lng = request.args.get('lng', '', type=float)
    name = request.args.get('name', '')
    return squarewheel.json_node_search(name, lat, lng)

@app.route('/foursquare/addcomment/', methods=['POST'])
def foursquare_addcomment():
    '''Adding new comments to foursquare venues'''
    
    foursquare_client = squarewheel.get_foursquare_client(session)[1]
    
    if request.is_xhr:
        venueId = request.form['venueid']
        text = request.form['text']
        if request.form['wheelmapid']:
            url = 'http://wheelmap.org/en/nodes/' + request.form['wheelmapid']
        else:
            url = False
        try:
            squarewheel.foursquare_add_comment(foursquare_client, venueId, text, url)
        except foursquare.Other, e:
            return jsonify(error=str(e))
        else:
            return jsonify(success=True)
        
        
@app.route('/foursquare')
def foursquare_callback():
    
    (fq_logged_in, foursquare_client) = squarewheel.get_foursquare_client(session)
    
    if not fq_logged_in:
    
        code = request.args.get('code', '')
               
        access_token = foursquare_client.oauth.get_token(code)
        
        foursquare_client.set_access_token(access_token)
                
        # Get the user id
        
        foursquare_id = foursquare_client.users()['user']['id']
        
         # <MongoDB>      
        connection = Connection(MONGODB_HOST, MONGODB_PORT)
        
        
        if MONGODB_NAME and MONGODB_PW:
            connection[MONGODB_DBNAME].authenticate(MONGODB_NAME, MONGODB_PW)
        
 
        session_key = uuid.uuid1()
        session['session_key'] = session_key
        collection = connection[MONGODB_DBNAME].users
        #user = {'_id': unicode(foursquare_id), 'session_key': unicode(session_key), 'access_token': unicode(access_token) }
        data = {'$set': {'session_key': unicode(session_key), 'access_token': unicode(access_token) } }
        #collection.insert(user)    
        collection.update({'_id': unicode(foursquare_id)}, data, upsert = True)
        # </MongoDB>
           
        foursquare_firstname, foursquare_icon = squarewheel.get_foursquare_user(foursquare_client)
        return render_template('start.html', foursquare_firstname=foursquare_firstname, foursquare_icon=foursquare_icon)
    else:
        return "Already logged in"

@app.route('/wheelmap/update_node/', methods=['POST'])
def wheelmap_update_node():
    if request.is_xhr:
        if squarewheel.update_wheelchair_status(request.form['wheelmapid'],
                                                request.form['wheelchairstatus']):
            return jsonify(success=True)
        else:
            abort(400)
            

app.secret_key = FLASK_SECRET_KEY


if __name__ == '__main__':
    app.debug = DEBUG # True or False
    if app.debug: #exception
        app.run()
    else:
        # Bind to PORT if defined, otherwise default to 5000.
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    
