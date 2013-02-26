import requests

# AUTH_ENDPOINT can also be https://foursquare.com/oauth2/authenticate
AUTH_ENDPOINT = 'https://foursquare.com/oauth2/authorize'
TOKEN_ENDPOINT = 'https://foursquare.com/oauth2/access_token'
VERSION = '20130128'
API_ENDPOINT = 'https://api.foursquare.com/v2/'

# These credentials have to be set from outside
cred = {
    'client_id': None,
    'client_secret': None,
    'redirect_uri': None
}

user = {
    'access_token': None
}

def set_credentials(client_id, client_secret, redirect_uri):
    cred.client_id = client_id
    cred.client_secret = client_secret
    cred.redirect_uri = redirect_uri
    
def oauth_url():
    parameters = (AUTH_ENDPOINT, cred.client_id, cred.client_secret, cred.redirect_uri)
    return '%s?client_id=%s&response_type=%s&redirect_uri%s' % parameters


def download_token(code):
    params = cred
    params['grant_type'] = authorization_code
    params['code'] = code    
    r = requests.get(TOKEN_ENDPOINT, params=params)
    user.access_token = r['access_token']
    return r['access_token']

def request(endpoint, params = {}):
    params['oauth_token'] = user.access_token
    uri = API_ENDPOINT + endpoint
    r = requests.get(uri, params=params)
    return r['response']
