import os
from urllib2 import urlopen
from urllib2 import unquote

import simple4sq as fq
from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import g
from flask import jsonify

import squarewheel
from os import environ as env

app = Flask(__name__)
app.config.from_object(__name__)
       
@app.route('/')
def startpage():

    # Check whether user wants to disconnect
    disconnect = request.args.get('disconnect', '', type=bool)
    if disconnect:
        squarewheel.user_disconnect()
    
    # Is the user is logged in transfer the username/icon
    if squarewheel.fq_logged_in():
        fq_firstname, fq_icon = squarewheel.get_fq_user()
    else:
        fq_firstname = False
        fq_icon = False
    return render_template('start.html', fq_oauth_url = fq.oauth_url(), fq_icon=fq_icon, fq_firstname=fq_firstname)

@app.route('/foursquare/addcomment/', methods=['POST'])
def fq_addcomment():
    '''Adding new comments to foursquare venues'''
    
    if request.is_xhr:
        venueId = request.form['venueid']
        text = request.form['text']
        # Link to Wheelmap included?
        if request.form['wheelmapid']:
            url = 'http://wheelmap.org/en/nodes/' + request.form['wheelmapid']
        else:
            url = False
        # Try to add the comment and send status response back
        try:
            squarewheel.fq_add_comment(venueId, text, url)
        except Exception, e:
            return jsonify(error=str(e))
        else:
            return jsonify(success=True)

@app.route('/foursquare/<path:endpoint>/', methods=['GET'])
def getvenues(endpoint):
    endpoint = endpoint.split('?')[0]
    page = request.args.get('page', '', type=int)
    if(endpoint == 'venues/explore'):
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
        
@app.route('/foursquare')
def fq_callback():
    
    fq_logged_in = squarewheel.fq_logged_in()
    
    if not fq_logged_in:
        code = request.args.get('code', '')
        # Log in the user and set the session_key for the user
        session['session_key'] = squarewheel.user_login(code)
        # Get name and icon for the user to show it
        fq_firstname, fq_icon = squarewheel.get_fq_user()
        return render_template('start.html', fq_firstname=fq_firstname, fq_icon=fq_icon)
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
            

app.secret_key = env['FLASK_SECRET_KEY']


if __name__ == '__main__':
    app.debug = 'DEBUG' in env # True or False
    if app.debug: #exception
        app.run()
    else:
        # Bind to PORT if defined, otherwise default to 5000.
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    
