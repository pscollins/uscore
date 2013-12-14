import facebook
import os

class BadEnvironmentError(Exception):
    pass

def get_graph_from_env():
    app_id = os.environ.get('FACEBOOK_APP_ID')
    app_secret = os.environ.get('FACEBOOK_APP_SECRET')
    if not (app_id and app_secret):
        raise BadEnvironmentError
    
    token = facebook.get_app_access_token(app_id, app_secret)
    assert(token)
    
    return facebook.GraphAPI(token)
