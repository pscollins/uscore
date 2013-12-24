'''Once we've gotten a big list of posts from the scraper, we process
it with everything in this file'''

import abc

class Adder(object):
    '''
    Abstract base class for UniqueAdder and Tabulator, mostly so that we
    can share private methods beween them
    '''
    
    @abc.abstractmethod
    def __init__(self):
        self.res = {}
    
    def _init_name(self, name):
        '''
        Sets up the result dictionary, res, to contain the key 'name',
        and sets all of the counters associated with the new name to 0
        '''
        
        self.res[name] = {}
        self.res[name]['in text count'] = 0
        self.res[name]['in text likes'] = 0
        self.res[name]['in comments count unique'] = 0
        self.res[name]['in comments count gross'] = 0
        self.res[name]['in comments likes'] = 0
        self.res[name]['likes given'] = 0
        self.res[name]['links given'] = 0
        self.res[name]['comments given'] = 0

    def _check_name(self, name):
        '''
        Checks to see if the result dictionary has the given name. If
        not, it adds it and initializes its counters to 0.
        '''
        try:
            self.res[name]
        except KeyError:
            self._init_name(name)

    def _inc(self, name, key):
        '''
        Increments a particular counter in the result dict of name,
        initializing all of name's counters to 0 if it isn't already
        present.
        '''
        self._check_name(name)
        self.res[name][key] += 1

class UniqueAdder(Adder):
    '''
    For a particular key of the tabulator, this object ensures that a
    given name is counted only once.
    '''
    def __init__(self, res, key):
        super().__init__()
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
            self.unique_likes += name
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
    ('in comment count unique')
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
    
    def __init__(self, posts, name_list):
        super().__init__()
        self.posts = posts
        self.names = name_list
        res = {}
        for name in name_list:
            self._init_name(name)

            
    def _update_in_text_count(self, post):
        '''
        Check for names that occur in the message of a post, and count
        the number of likes that they recieve.
        '''
        for name in self.names:
            if name in post.message:
                self.res[name]['in text count'] += 1
                self.res[name]['in text likes'] += self._update_likes(post)

    def _update_in_comments_count(self, post):
        '''
        Check to see which names were lnked in comments,
        and the number of commens they recieved.
        Also increment the 'links given' of the linker,
        and the 'comments given' of any commentors.
        '''
        adder = UniqueAdder(self, 'in comments count unique')
        for comment in post.comments:
            self._inc(comment['from']['name'], 'comments given')
            for tag in comment['message_tags']:
                name = tag['name']
                adder.add(name)
                self._inc(name, 'in comments count gross')
                self.res[name]['in comments likes'] += comment['like_count']
                self.res[name]['links given'] += 1
                
    def _update_likes(self, post):
        '''
        Update the 'likes given' counter for everyone who liked
        a post, then return the total likes on it.
        '''
        for name in post.likes:
            self._inc(name, 'likes given')
        return len(post.likes)

    def _update(self, post):
        '''
        Parse a single post and update all counters.
        '''
        self._update_in_text_count(post)
        self._update_in_comments_count(post)

    def tabulate(self):
        '''
        Calculate all of the necessay statistics for each post.
        '''
        for post in self.posts:
            self._update(post)
        return self.res
