'''The purpose of this module is to implement all of the parts of scoreboard that need to talk to the Facebook API.'''

import datetime
import facebook
import os

import pdb

class BadEnvironmentError(Exception):
    pass

class GraphAPIError(Exception):
    pass

class BadRequestError(GraphAPIError):
    def __init__(self, error_dict):
        super().__init__()
        self.error_dict = error_dict['error']

    def __str__(self):
        ret = '''Message: {}
        Type: {}
        Code: {}'''.format(self.error_dict['message'],
                           self.error_dict['type'],
                           self.error_dict['code'])

        return ret

class EmptyResponseError(GraphAPIError):
    pass

class BadDateError(GraphAPIError):
    pass

class EmptyQueryError(GraphAPIError):
    pass

# def substr_in_list(s, l):
#     for item in l:
#         if s in item:
#             return True

#     return False

def try_del(d, *args):
    for key in args:
        try:
            del d[key]
        except KeyError:
            pass

    return d

class GraphObject:
    def _check_for_error(self, resp):
        if 'error' in resp.keys():
            raise BadRequestError(resp)
        if 'data' in resp.keys() and not resp['data']:
            raise EmptyResponseError
        else:
            return resp

class Query(GraphObject):
    DEFAULT_LIMIT = 500
    
    def __init__(self, page, name, last_date=0, **kwargs):
        
        self._page = page
        self._init_args = kwargs
        self.last_date = last_date
        self.name = name
        self.resp = {}
        
    def query(self, **kwargs):
        resp = self._page.graph.get_connections(self._page.page_id,
                                               self.name, **kwargs)
        self.resp = self._check_for_error(resp)
        
        return resp

    #TODO: this needs to do something sane if 'paging' isn't in the resp
    @property
    def next_args(self):
        return self._get_args('next')

    @property
    def prev_args(self):
        return self._get_args('previous')
    
    
    def _get_args(self, direction):
        try:
            return self._proc_args(self.resp['paging'][direction])
        except KeyError:
            return None
    
    def _proc_args(self, query_url, *args):
        args_list = [e.split('=') for e in query_url.split('?', 1)[-1].split('&')]
        ret = {key:value for key, value in args_list}
        if not 'limit' in ret.keys():
            ret['limit'] = self.DEFAULT_LIMIT
            
        return ret
        
    def next(self):
        # check for failure conditions and raise exceptions if something will
        # give us an invalid result.
        # We care about this in particular so that the iterator can capture
        # them later.
        if self.next_args:
            if int(self.next_args['until']) < self.last_date:
                raise BadDateError
            if self.next_args['until'] == self.prev_args['since']:
                raise EmptyQueryError

        if not self.resp:
                self.resp = self.query(**self._init_args)
        elif self.next_args:
                self.resp = self.query(**self.next_args)
        else:
            # we only hit this branch if we don't have 'next' args to go to
            # and we're not on our first query
            raise EmptyQueryError

        return self.resp

    def __iter__(self):
        return IterableQuery(self)

    
# I'm not sure if this is considered good style?
# Anyway, it will be opaque to any calling code so I can go back and add in
# a __next__ to Query later on in life if it turns out to be annoying
class IterableQuery:
    def __init__(self, query):
        self._query = query

    def __next__(self):
        ret = {}
        try:
            ret = self._query.next()
            
        except (EmptyResponseError, BadDateError, EmptyQueryError):
            raise StopIteration
        
        return ret
        
    
class Page(GraphObject):
    def __init__(self, graph, page_id):
        assert type(page_id) is str
        
        self.graph = graph
        self.page_id = page_id

        self._check_for_error(self.graph.get_object(page_id))

    # This very well may be evil.    
    def __getattr__(self, name):
        return lambda **kwargs: Query(self, name, **kwargs)
    
    
class Scraper:
    # delay between successive scrapes
    DELAY = 3600
    def __init__(self, page_id, name_list=None, graph_source=None):
        if not graph_source:
            graph = self._get_graph_from_env()
        else:
            # implement me later
            pass

        self.posts = {}
        # last_scraped holds the unix timestamp when the last scraping happened
        self.last_scraped = 0
        self.page = Page(graph, page_id)
        

    def _get_graph_from_env(self):
        app_id = os.environ.get('FACEBOOK_APP_ID')
        app_secret = os.environ.get('FACEBOOK_APP_SECRET')
        if not (app_id and app_secret):
            raise BadEnvironmentError

        token = facebook.get_app_access_token(app_id, app_secret)
        assert(token)
        
        return facebook.GraphAPI(token)
            
                
    def update_scoreboard(self, num_to_proc=float("inf"), **kwargs):
        # TODO: currently, this gets stuck around June because the Graph API
        # rolls lke that for whatever reason. Need to add in an override that
        # says "even if you're not getting anything in response, keep hitting
        # until you arrive at this date"
        now = datetime.datetime.now().timestamp()

        if self.last_scraped < (now + self.DELAY):
            self.last_scraped = now
            self.posts = []
            # NOTE: this is going to be REALLY EXPENSIVE
            # Also, it would parallelize easily, IF we knew how many queries it
            # would take to get to the end of self.page.posts
            for posts in self.page.posts(**kwargs):
                self.posts += posts['data']
                if not num_to_proc:
                    break
                num_to_proc -= 1


        return self.posts
        
