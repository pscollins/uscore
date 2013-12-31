'''The purpose of this module is to implement all of the parts of
scoreboard that need to talk to the Facebook API.'''

import collections
import facebook
import os
import simplejson
import urllib.parse
from concurrent import futures


class BadEnvironmentError(Exception):
    pass

class GraphAPIError(Exception):
    def __str__(self):
        return self.__class__.__name__

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
    '''
    Represents a query on the graph API. Provides generator syntax (for x in
    query...).
    '''
    DEFAULT_LIMIT = '500'
    # step backwards to take if last_date has been set, in seconds
    STEP = 259200
    MAX_RETRIES = 10

    
    def __init__(self, page, name, **kwargs):
        print("query initialized: ", page, name, kwargs)        
        self._page = page
        
        try:
            self.last_date = kwargs.pop('last_date')
        except KeyError:
            self.last_date = None

        # we overwrite the default limit if it's been passed in kwargs
        self._init_args = {'limit':self.DEFAULT_LIMIT}
        self._init_args = kwargs

        self.name = name
        self.resp = {}
        
    def query(self, **kwargs):
        # print('about to query: ', self._page.obj_id, self.name, kwargs)
        resp = self._page.graph.get_connections(self._page.obj_id,
                                                self.name, **kwargs)
        self.resp = self._check_for_error(resp)
        # print(resp)
        return resp

    @property
    def next_args(self):
        return self._get_args('next')

    # @property
    # def prev_args(self):
    #     return self._get_args('previous')
    
    
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

        # this might be causing an issue -- it's also already handled by
        # the facebook module
        if 'access_token' in ret.keys():
            del(ret['access_token'])
            
        return ret

    def _check_next_args(self):
        # print('next_args: ', self.next_args.keys())  
        if 'until' in self.next_args.keys():
            next_key, prev_key = 'until', 'since'
            if (self.last_date is not None) and \
              (int(self.next_args[next_key]) < self.last_date):
                raise BadDateError
        elif 'after' in self.next_args.keys():
            next_key, prev_key = 'after', 'before'
        else:
            # NB: this is not really the right exception, but i don't think it
            # makes sense to define a new one
            raise BadDateError
        
    
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
        return self

    def __next__(self):
        args = {}
        for i in range(0, self.MAX_RETRIES):
            try:
                return self.next(**args)
            except (BadDateError, EmptyQueryError) as e:
                # print("stopped because ", e)
                raise StopIteration
            except EmptyResponseError:
                # override and force a new query with the next date
                # if it's been set
                # we need to do this because the 'next' cursor that the Graph
                # API gives us randomly fail to produce any results
                print('Manually decrementing the request date.')
                if self.last_date is not None:
                    args = self.next_args if not args else args
                    args['until'] = str(int(args['until']) - self.STEP)
                else:
                    # print('raising StopIteration again')
                    raise StopIteration
            except BadRequestError as e:
                print('An error occurred: ')
                print(e)
                print('Retrying (attempt {}/{})'.format(i+1, self.MAX_RETRIES))
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

# lighweight, serializable namedtuple for our posts
Post = collections.namedtuple('Post',
                              field_names=('message', 'comments', 'likes'))

# and a builder class carries around the GraphAPI objects we need to make
# queries.     
class PostBuilder:
    '''Class for organizing data returned from facebook wall posts. If a
Graph object is passed, it will perform a "deep check" and pull down all
of the comments and likes.'''
    
    def __init__(self, graph=None):
        # print(post_dict)
        self._graph = graph
        # print('graph :', graph)
    
    def create(self, post_dict):
        ret = {}
                
        try:
            ret['message'] = post_dict['message']
        except KeyError:
            ret['message'] = ''

        deep_update = lambda key: self._deep_update(post_dict, key)

        with futures.ThreadPoolExecutor(max_workers=3) as executor:
            updates = {executor.submit(deep_update, key):key for key in
                       ('comments', 'likes')}
            for future in futures.as_completed(updates):
                key = updates[future]
                ret[key] = future.result()
                
                
            # comments = self._deep_update('comments')
            # likes = self._deep_update('likes')

        return Post(**ret)

    def _get_post(self, post_id):
        return GraphObject(self._graph, post_id)
            
    def _needs_deep_update(self, post_dict, key):
        unique_cursors = len(set(post_dict[key]['paging']['cursors'].values()))
        if self._graph and unique_cursors > 1:
            return True
        return False

    
    def _deep_update(self, post_dict, key):
        ret = []
        # if there are no comments/likes, the response doesn't contain the key
        # 'comments' or 'likes', so we need to check for that and return an
        # empty list if it doesn't
        if key in post_dict.keys():
            if self._needs_deep_update(post_dict, key):
                post_graph_obj = self._get_post(post_dict['id'])
                for el in getattr(post_graph_obj, key)():
                    ret.extend(el['data'])
            else:
                # print('other yes')
                ret = post_dict[key]['data']
        return ret

    @staticmethod
    def posts_to_file(posts, file_handle):
        simplejson.dump(posts, file_handle)
        

    @staticmethod
    def posts_from_file(file_handle):
        return [Post(p['message'], p['comments'], p['likes'])
               for p in simplejson.load(file_handle)]        
        
    
class Scraper:
    # delay between successive scrapes, in seconds
    DELAY = 3600

    # MAX_WORKERS = 50
    
    def __init__(self, page_id, access_token=None, max_workers=50):
        if not access_token:
            self._graph = self._get_graph_from_env()
        else:
            self._graph = facebook.GraphAPI(access_token)

        self.max_workers=max_workers
            
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

    def _build_posts(self, post_builder, post_list):
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as \
          executor:
            async_build = lambda p: executor.submit(post_builder.create, p)
            post_futures = [async_build(p) for p in post_list]
            ret = [p.result() for p in futures.as_completed(post_futures)]
            
        return ret

                
    def update_scoreboard(self, num_to_proc=float("inf"),
                          deep=False, source=None, **kwargs):
        
        # if self.last_scraped < (now + self.DELAY):
        # self.last_scraped = now
        self.posts = []
        # print('kwargs: ', kwargs)

        
        post_builder = PostBuilder(self._graph if deep else None)

        if source:
            post_fetcher = getattr(self.page, source)(**kwargs)
        else:
            post_fetcher = self.page.feed(**kwargs)
                
            # NOTE: this is going to be REALLY EXPENSIVE
            # Also, it would parallelize easily, IF we knew how many queries it
            # would take to get to the end of self.page.posts
        for posts in post_fetcher:
            # print("posts: ", posts)
            self.posts.extend(self._build_posts(post_builder, posts['data']))
            
            if not num_to_proc:
                break
            num_to_proc -= 1


        return self.posts
        
