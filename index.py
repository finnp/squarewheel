from flask import Flask
from flask import render_template
from flask import request
from flask import session
from urllib2 import urlopen
import json
import squarewheel

app = Flask(__name__)

@app.before_request
def before_request():
    
    if 'foursquare_token' in session:
        session['foursquare_enabled'] = True
    else:
        session['foursquare_enabled'] = False
    
    if not 'foursquare_icon' in session:
        session['foursquare_enabled'] = False
        session['foursquare_icon'] = None
        session['foursquare_firstname'] = None
    

@app.route('/')
def startpage():
    return render_template('city_search.html', title="Welcome!")
    
@app.route('/foursquare/venues/explore/<city>')
def explore_city(city):
    venues = squarewheel.explore_foursquare(city)
    return render_template('venue_list.html', venues=venues)

@app.route('/foursquare/venues/lastcheckins')
def lastcheckins():
    # Change this and comminicate with Javascript
    if not 'foursquare_token' in session:
        return ""
    
    venues = squarewheel.get_last_foursquare_checkins(session['foursquare_token'])
    return render_template('venue_list.html', venues=venues)
    

@app.route('/foursquare/venues/todo')
def todo():
    if not 'foursquare_token' in session:
        return ""
        
    venues = squarewheel.get_todo_venues(session['foursquare_token'])
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
    uri= "https://foursquare.com/oauth2/access_token"
    uri += "?client_id=%s" %  squarewheel.foursquare_client_id
    uri += "&client_secret=%s" % squarewheel.foursquare_client_secret
    uri += "&grant_type=authorization_code"
    uri += "&redirect_uri=%s" % squarewheel.foursquare_callback_url
    uri += "&code=%s" % code
    response = urlopen(uri).read()    
    token = json.loads(response)["access_token"]
    session['foursquare_token'] = token
    (session['foursquare_firstname'], session['foursquare_icon']) = squarewheel.get_foursquare_user(token)
    session['foursquare_enabled'] = True
    return render_template('city_search.html', title="Your account is connected, start browsing!")

@app.route('/disconnect')
def foursquare_disconnect():
    session.pop('foursquare_token', None)
    session.pop('foursquare_icon', None)
    session.pop('foursquare_enabled', None)
    return "Session cleared"

app.secret_key = "\xfa\xdek\xfc\xce\xa5\x07I\xa1\xf6\xe2a\x08\xf4I\x92Ye\xdd\x15\x98h8n"

if __name__ == '__main__':
    app.debug = True
    #app.debug = False
    if app.debug:
        app.run()
    else:
        app.run(host='0.0.0.0')
    
