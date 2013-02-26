import requests

# AUTH_ENDPOINT can also be https://foursquare.com/oauth2/authenticate
AUTH_ENDPOINT = 'https://foursquare.com/oauth2/authorize'
TOKEN_ENDPOINT = 'https://foursquare.com/oauth2/access_token'
VERSION = '20130128'
API_ENDPOINT = 'https://api.foursquare.com/v2/'

# These credentials have to be set from outside
cred = {
    'client_id': False,
    'client_secret': False,
    'redirect_uri': False
}

user = {
    'access_token': False
}

def set_credentials(client_id, client_secret, redirect_uri):
    cred['client_id'] = client_id
    cred['client_secret'] = client_secret
    cred['redirect_uri'] = redirect_uri
    
def oauth_url():
    parameters = (AUTH_ENDPOINT, cred['client_id'], cred['redirect_uri'])
    return '%s?client_id=%s&response_type=code&redirect_uri=%s' % parameters


def download_token(code):
    params = cred
    params['grant_type'] = 'authorization_code'
    params['code'] = code    
    r = requests.get(TOKEN_ENDPOINT, params=params)
    
    print 'GET: ' + r.url
    
    json = r.json()
    
    if 'error' in json:
        raise Exception(json['error'])
     
    user['access_token'] = json['access_token'] 
    return json['access_token'] 

def request(endpoint, params = {}, method = 'GET'):
    # If there is an access_token, use it, otherweise try userless
    if user['access_token']:
        params['oauth_token'] = user['access_token']
    else:
        params['client_id'] = cred['client_id']
        params['client_secret'] = cred['client_secret']
    
    params['v'] = VERSION
    
    uri = API_ENDPOINT + endpoint
    
    if method == 'POST':
        r = requests.post(uri, params=params)
    else:
        r = requests.get(uri, params=params)
    
    print 'GET: ' + r.url
    
    json = r.json()
    
    if json['meta']['code'] != 200:
        raise Exception(json['meta']['errorDetail'])

    return json['response']
