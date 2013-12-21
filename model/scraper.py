'''The purpose of this module is to implement all of the parts of
scoreboard that need to talk to the Facebook API.'''

import datetime
import facebook
import os
import urllib.parse


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

class AbstractGraphObject:
    def _check_for_error(self, resp):
        if 'error' in resp.keys():
            raise BadRequestError(resp)
        if 'data' in resp.keys() and not resp['data']:
            raise EmptyResponseError
        else:
            return resp

class Query(AbstractGraphObject):
    DEFAULT_LIMIT = 500
    
    def __init__(self, page, name, last_date=0, **kwargs):
        # print("query initialized: ", page, name, last_date, kwargs)        
        self._page = page
        self._init_args = kwargs
        self.last_date = last_date
        self.name = name
        self.resp = {}
        
    def query(self, **kwargs):
        # print('about to query: ', self._page.obj_id, self.name, kwargs)
        resp = self._page.graph.get_connections(self._page.obj_id,
                                                self.name, **kwargs)
        self.resp = self._check_for_error(resp)
        
        return resp

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
    
    def _proc_args(self, query_url):
        # args_list = [e.split('=') for e in \
        #              query_url.split('?', 1)[-1].split('&')]
        
        ret = {key:value[0] for key, value in \
            urllib.parse.parse_qs(query_url.split('?', 1)[-1]).items()}
        if not 'limit' in ret.keys():
            ret['limit'] = self.DEFAULT_LIMIT

        # this might be causing an issue -- it's also alread handled by
        # the facebook module
        if 'access_token' in ret.keys():
            del(ret['access_token'])
            
        return ret

    def _check_next_args(self):
        # print('next_args: ', self.next_args.keys())  
        if 'until' in self.next_args.keys():
            next_key, prev_key = 'until', 'since'
            if int(self.next_args[next_key]) < self.last_date:
                raise BadDateError
        elif 'after' in self.next_args.keys():
            next_key, prev_key = 'after', 'before'
        else:
            # NB: this is not really the right exception, but i don't think it
            # makes sense to define a new one
            raise BadDateError
        # if self.resp and len(set(self.resp['paging']['cursors']
        # TODO: this is erroring
        # if self.next_args[next_key] == self.prev_args[prev_key]:
            # raise EmptyQueryError

    
    def next(self, **kwargs):
        args = {}
        
        # check for failure conditions and raise exceptions if something will
        # give us an invalid result.
        # We care about this in particular so that the iterator can capture
        # them later.
        if self.next_args:
            self._check_next_args()

        # order is important:
        # first, check to see if custom args have been given, use them if they
        # have.
        # next, check if we've made a query before, if not, build the inital
        # arguments.
        # next, try to pull the args out of the query
        # if nothing has worked, raise EmptyQueryError
        if kwargs:
            args = kwargs
        elif not self.resp:
            args = self._init_args
        elif self.next_args:
            args = self.next_args
        else:
            # we only hit this branch if we don't have 'next' args to go to
            # and we're not on our first query, and no custom args have been
            # given
            raise EmptyQueryError

        self.resp = self.query(**args)
        return self.resp

    def __iter__(self):
        return IterableQuery(self)

    
# I'm not sure if this is considered good style?
# Anyway, it will be opaque to any calling code so I can go back and add in
# a __next__ to Query later on in life if it turns out to be annoying
class IterableQuery:
    # step backwards to take if last_date has been set
    STEP = 259200
    def __init__(self, query):
        self._query = query

    def __next__(self):
        # is this ugly? we need it to keep trying until it fails, and this
        # saves us recursion + an argument to __next__
        while True:
            args = {}
            try:
                return self._query.next(**args)
            except (BadDateError, EmptyQueryError) as e:
                # print("stopped because ", e)
                raise StopIteration
            except EmptyResponseError:
                # override and force a new query with the next date
                # if it's been set
                # this isn't going to loop infinitely because eventually
                # BadDateError will be raised
                # we need to do this because the 'next' cursor that the Graph
                # API gives us randomly fail to produce any results
                if self._query.last_date:
                    args = self._query.next_args
                    args['until'] -= self.STEP
                else:
                    raise StopIteration
        
    
class GraphObject(AbstractGraphObject):
    def __init__(self, graph, obj_id):
        assert type(obj_id) is str
        
        self.graph = graph
        self.obj_id = obj_id

    # This very well may be evil.
    def __getattr__(self, name):
        return lambda **kwargs: Query(self, name, **kwargs)

    def __repr__(self):
        return "GraphObject: ({}, {})".format(self.graph, self.obj_id)

class Post:
    '''Class for organizing data returned from facebook wall posts. If a
Graph object is passed, it will perform a "deep check" and pull down all
of the comments and likes.'''
    def __init__(self, post_dict, graph=None):
        # print(post_dict)
        self._post_dict = post_dict
        self._graph = graph
        self._post_id = post_dict['id']
        # print('graph :', graph)
        
        self.comments = self._deep_update('comments')
        self.likes = self._deep_update('likes')

        try:
            self.message = post_dict['message']
        except KeyError:
            self.message = ''

    def __repr__(self):
        fmt = 'Message: {}\nLikes: {}\nComments: {}'
        return fmt.format(self.message, self.likes, self.comments)

    #lazy initialization because we hit the page
    @property
    def _post(self):
        if not hasattr(self, '__post'):
            self.__post = GraphObject(self._graph, self._post_id)
        return self.__post
            
    def _needs_deep_update(self, key):
        unique_cursors = \
          len(set(self._post_dict[key]['paging']['cursors'].values()))
        # print('unique cursors: ', unique_cursors)
        # print('cursors: ', set(self._post_dict[key]['paging']['cursors'].values()))
        # print('u_c > 1?', unique_cursors > 1)
        if self._graph and unique_cursors > 1:
            return True
        return False

    
    def _deep_update(self, key):
        ret = []
        # if there are no comments/likes, the response doesn't contain the key
        # 'comments' or 'likes', so we need to check for that and return an
        # empty list if it doesn't
        if key in self._post_dict.keys():
            # print(key, ": ", self._post_dict[key]['data'])
            # print("yes1")
            if self._needs_deep_update(key):
                # print("yes2", key)
                # print(self._post, getattr(self._post, key), getattr(self._post, key)())
                # print(getattr(self._post, key)().next())
                for elements in getattr(self._post, key)():
                    # print('in loop')
                    # print(key, ": ", elements['data'])
                    ret += elements['data']
            else:
                # print('other yes')
                ret = self._post_dict[key]['data']
                    
        return ret
        
    
class Scraper:
    # delay between successive scrapes
    DELAY = 3600
    def __init__(self, page_id, access_token=None):
        if not access_token:
            self._graph = self._get_graph_from_env()
        else:
            self._graph = facebook.GraphAPI(access_token)


        self.posts = {}
        # last_scraped holds the unix timestamp when the last scraping happened
        self.last_scraped = 0
        self.page = GraphObject(self._graph, page_id)
        

    def _get_graph_from_env(self):
        app_id = os.environ.get('FACEBOOK_APP_ID')
        app_secret = os.environ.get('FACEBOOK_APP_SECRET')
        if not (app_id and app_secret):
            raise BadEnvironmentError

        token = facebook.get_app_access_token(app_id, app_secret)
        assert(token)
        
        return facebook.GraphAPI(token)
            
                
    def update_scoreboard(self, num_to_proc=float("inf"),
                          deep=False, source=None, **kwargs):
        # TODO: currently, this gets stuck around June because the Graph API
        # rolls lke that for whatever reason. Need to add in an override that
        # says "even if you're not getting anything in response, keep hitting
        # until you arrive at this date"
        now = datetime.datetime.now().timestamp()

        if self.last_scraped < (now + self.DELAY):
            self.last_scraped = now
            self.posts = []

            post_constructor = lambda p: Post(p, self._graph) if deep else Post

            if source:
                post_fetcher = getattr(self.page, source)(**kwargs)
            else:
                post_fetcher = self.page.feed(**kwargs)
                
            # NOTE: this is going to be REALLY EXPENSIVE
            # Also, it would parallelize easily, IF we knew how many queries it
            # would take to get to the end of self.page.posts
            for posts in post_fetcher:
                # print("posts: ", posts)
                self.posts += [post_constructor(p) for p in posts['data']]
                if not num_to_proc:
                    break
                num_to_proc -= 1


        return self.posts
        
