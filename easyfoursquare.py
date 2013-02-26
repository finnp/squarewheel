import requests

# AUTH_ENDPOINT can also be https://foursquare.com/oauth2/authenticate
AUTH_ENDPOINT = 'https://foursquare.com/oauth2/authorize'
TOKEN_ENDPOINT = 'https://foursquare.com/oauth2/access_token'
VERSION = "20130128"

# These credentials have to be set from outside
cred = {
    'client_id': None,
    'client_secret': None,
    'redirect_uri': None
}

user = {
    'access_token': None
}

    
def oauth_url():
    parameters = (AUTH_ENDPOINT, cred.client_id, cred.client_secret, cred.redirect_uri)
    return '%s?client_id=%s&response_type=%s&redirect_uri%s' % parameters


def get_token(code):
    params = cred
    params['grant_type'] = authorization_code
    params['code'] = code    
    r = requests.get(TOKEN_ENDPOINT, params=params)
    return r['access_token']
