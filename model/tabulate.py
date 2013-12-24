'''Once we've gotten a big list of posts from the scraper, we process
it with everything in this file'''

import abc


def _check_invariants(f):
    def inner(self, *args, **kwargs):
        # print('in ', f)
        # print('res: ', self.res)
        assert isinstance(self.res, dict)
        for key, value in self.res.items():
            assert isinstance(value, dict)
            
        ret = f(self, *args, **kwargs)
        assert isinstance(self.res, dict)
        for key, value in self.res.items():
            assert isinstance(value, dict)

        # print('out ', f)
        # print('res: ', self.res)
        return ret
    return inner


class Adder(object):
    '''
    Abstract base class for UniqueAdder and Tabulator, mostly so that we
    can share private methods beween them
    '''
    KEYS = ['in text count', 'in text likes', 'in comments count unique',
            'in comments count gross', 'in comments likes', 'likes given',
            'links given', 'comments given']
    
    @abc.abstractmethod
    def __init__(self):
        self.res = {}

    @_check_invariants
    def _init_name(self, name):
        '''
        Sets up the result dictionary, res, to contain the key 'name',
        and sets all of the counters associated with the new name to 0
        '''
        
        self.res[name] = {}
        for key in self.KEYS:
            self.res[name][key] = 0
        # self.res[name]['in text count'] = 0
        # self.res[name]['in text likes'] = 0
        # self.res[name]['in comments count unique'] = 0
        # self.res[name]['in comments count gross'] = 0
        # self.res[name]['in comments likes'] = 0
        # self.res[name]['likes given'] = 0
        # self.res[name]['links given'] = 0
        # self.res[name]['comments given'] = 0

    @_check_invariants
    def _check_name(self, name):
        '''
        Checks to see if the result dictionary has the given name. If
        not, it adds it and initializes its counters to 0.
        '''
        # print('checking: ', name)
        assert isinstance(name, str)
        try:
            self.res[name]
        except KeyError:
            self._init_name(name)

    @_check_invariants
    def _inc(self, name, key):
        '''
        Increments a particular counter in the result dict of name,
        initializing all of name's counters to 0 if it isn't already
        present.
        '''
        self._check_name(name)
        self.res[name][key] += 1

    # def merge_with(self, res):
    #     assert res.keys() == self.res.keys()
    #     for name in res1:
    #         for key in self.KEYS
            
        
        

class UniqueAdder(Adder):
    '''
    For a particular key of the tabulator, this object ensures that a
    given name is counted only once.
    Accepts a *reference to* a dictionary to be updated in the process.
    This saves us the hassle of merging the results after.
    '''
    def __init__(self, res, key):
        super().__init__()

        assert isinstance(res, dict)
        
        self.res = res
        self.key = key
        self.unique_likes = set()

    def add(self, name):
        '''
        Checks to see if the given name has been counted already. If
        not, it increments the counter in question (specified as the
        key supplied when initializing the object.
        '''
        if not name in self.unique_likes:
            self.unique_likes.add(name)
            self._inc(name, self.key)
            
class Tabulator(Adder):
    '''
    Given Post objects and a list of names, calculate the following for each
    name:
    The number of times the name appeared in the body of a message
    ('in text count')
    The number of likes that it recieved when it did
    ('in text likes')
    The number of posts in which it was linked in a comment
    ('in comments count unique')
    The number of times that it was linked in a comment, total
    ('in comments count gross')
    The number of likes that it recieved when linked in a comment
    ('in comments likes')
    The number of times it liked a post's message
    ('likes given')
    The number of times it linked someone else in a comment
    ('links given')
    The number of times that it commented
    ('comments given')
    '''
    
    def __init__(self, posts, names):
        super().__init__()
        self.posts = posts
        self.names = set(names) # remove duplicates
        for name in self.names:
            self._init_name(name)

    @_check_invariants
    def _update_in_text_count(self, post):
        '''
        Check for names that occur in the message of a post, and count
        the number of likes that they recieve.
        '''
        for name in self.names:
            if name in post.message:
                # print('_in_text_count: ', name)
                self.res[name]['in text count'] += 1
                self.res[name]['in text likes'] += self._get_num_likes(post)

    @_check_invariants
    def _update_in_comments_count(self, post):
        '''
        Check to see which names were lnked in comments,
        and the number of commens they recieved.
        Also increment the 'links given' of the linker,
        and the 'comments given' of any commentors.
        '''
        adder = UniqueAdder(self.res, 'in comments count unique')
        for comment in post.comments:
            sender = comment['from']['name']
            self._inc(sender, 'comments given')
            try:
                for tag in comment['message_tags']:
                    print('tag: ', tag)
                    recipient = tag['name']
                    adder.add(recipient)
                    self._inc(recipient, 'in comments count gross')
                    self.res[recipient]['in comments likes'] += \
                      comment['like_count']
                    self.res[sender]['links given'] += 1
            except KeyError:
                pass
            
    @_check_invariants
    def _update_likes(self, post):
        '''
        Update the 'likes given' counter for everyone who liked
        a post.
        '''
        # print(post.likes)
        for like in post.likes:
            # print(like)
            self._inc(like['name'], 'likes given')

    def _get_num_likes(self, post):
        '''
        Get the number of likes for the post.
        '''
        return len(post.likes)

    @_check_invariants
    def _update(self, post):
        '''
        Parse a single post and update all counters.
        '''
        self._update_in_text_count(post)
        self._update_in_comments_count(post)
        self._update_likes(post)

    @_check_invariants
    def tabulate(self):
        '''
        Calculate all of the necessay statistics for each post.
        '''
        for post in self.posts:
            self._update(post)
        return self.res



#http://stackoverflow.com/questions/6307761/how-can-i-decorate-all-
#functions-of-a-class-without-typing-it-over-and-over-for
# def _for_all_methods(decorator):
#     def decorate(cls):
#         for attr in cls.__dict__:
#             if callable(getattr(cls, attr)) and '__' not in attr:
#                 setattr(cls, attr, decorator(getattr(cls, attr)))
#         return cls
#     return decorate
