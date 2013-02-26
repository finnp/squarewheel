from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import g
from flask import jsonify
from urllib2 import urlopen
from urllib2 import unquote
import os
import json
import squarewheel
import easyfoursquare as fq
import foursquare
import logging
from config import FLASK_SECRET_KEY
from config import DEBUG

app = Flask(__name__)
app.config.from_object(__name__)
       
@app.route('/')
def startpage():

    disconnect = request.args.get('disconnect', '', type=bool)
    if disconnect:
        squarewheel.user_disconnect()
    
    if not request.is_xhr:
        fq_logged_in = squarewheel.fq_logged_in()
        if fq_logged_in:
            foursquare_firstname, foursquare_icon = squarewheel.get_foursquare_user()
            foursquare_oauth_url = False
        else:
            foursquare_oauth_url = fq.oauth_url()
            foursquare_firstname = False
            foursquare_icon = False
    else:
        foursquare_oauth_url = False
        foursquare_firstname = False
        foursquare_icon = False
    return render_template('start.html', foursquare_oauth_url = foursquare_oauth_url, foursquare_icon=foursquare_icon, foursquare_firstname=foursquare_firstname)

@app.route('/foursquare/<endpoint>')
def getvenues(endpoint):
    page = request.args.get('page', '', type=int)
    if(endpoint == 'explore'):
        geolocation = request.args.get('geolocation', '')
        query = request.args.get('query', '')
        page = request.args.get('page', '', type=int)
        params = {'near': unquote(geolocation).encode('utf-8')}
        if query:
            params['query'] = unquote(query).encode('utf-8')
    else:
        params = {}
    
    fq_logged_in = squarewheel.fq_logged_in()
    
    try:
        venues = squarewheel.get_venues(endpoint, page, params)
    except Exception, e:
        return str(e), 500
    else:
        return render_template('venue_list.html', venues=venues, fq_logged_in = fq_logged_in)

@app.route('/wheelmap/nodes')
def get_nodes():
    lat = request.args.get('lat', '', type=float)
    lng = request.args.get('lng', '', type=float)
    name = request.args.get('name', '')
    return squarewheel.json_node_search(name, lat, lng)

@app.route('/foursquare/addcomment/', methods=['POST'])
def foursquare_addcomment():
    '''Adding new comments to foursquare venues'''
    
    if request.is_xhr:
        venueId = request.form['venueid']
        text = request.form['text']
        if request.form['wheelmapid']:
            url = 'http://wheelmap.org/en/nodes/' + request.form['wheelmapid']
        else:
            url = False
        try:
            squarewheel.foursquare_add_comment(venueId, text, url)
        except foursquare.Other, e:
            return jsonify(error=str(e))
        else:
            return jsonify(success=True)
        
        
@app.route('/foursquare')
def foursquare_callback():
    
    fq_logged_in = squarewheel.fq_logged_in()
    
    if not fq_logged_in:
    
        code = request.args.get('code', '')
        
        # Set the access_token       
        fq.download_token(code)
                   
        session['session_key'] = squarewheel.user_login()

        foursquare_firstname, foursquare_icon = squarewheel.get_foursquare_user()
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
    
