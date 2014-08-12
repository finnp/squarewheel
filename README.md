# SQUAREWHEEL

Squarewheel aims to be a connection between the venue database of
foursquare and the nodes database of wheelmape (openstreetmap).

For example user should be able to check how foursquare venues are rated
for accessibility on foursquare or have the opportunity to rate places
they have been and checked in with foursquare.

The site is currently running on http://squarewheel.herokuapp.com/

## Install

### Set the following env variables:
```
export WHEELMAP_API_KEY=xxx
# export WHEELMAP_API_KEY_VISITOR_EDITS=xxx

export FOURSQUARE_CLIENT_ID=xxx
export FOURSQUARE_CLIENT_SECRET=xxx
export FOURSQUARE_CALLBACK_URL=xxx

# Set this to a fixed random value, e.g. os.urandom(24)
export FLASK_SECRET_KEY=xxx

# MongoDB configuration
export MONGODB_HOST=localhost
export MONGODB_PORT=27017
export MONGODB_DBNAME=squarewheel

#export MONGODB_NAME=xxx
#export MONGODB_PW=xxx

export DEBUG=1
```

### Get it running
```
$ # Install virtualenv (pip install)
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```