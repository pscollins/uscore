'''Once we've gotten a big list of posts from the scraper, we process
it with everything in this file'''

import abc

class Adder:
    '''Abstract base class for UniqueAdder and Tabulator, mostly so that we can share private methods beween them'''
    
    @abc.abstractmethod
    def __init__(self):
        self.res = {}
    
    def _init_name(self, name):
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
        try:
            self.res[name]
        except KeyError:
            self._init_name(name)

    def _inc(self, name, key):
        self._check_name(name)
        self.res[name][key] += 1


class UniqueAdder(Adder):
    def __init__(self, res, key):
        super().__init__()
        self.res = res
        self.key = key
        self.unique_likes = set()

    def add(self, name):
        if not name in self.unique_likes:
            self.unique_likes += name
            self._inc(self.res, name, self.key)
            

class Tabulator(Adder):
    def __init__(self, posts, name_list):
        super().__init__()
        self.posts = posts
        self.names = name_list
        for name in name_list:
            self._init_name(name)

            
    def _update_in_text_count(self, post):
        for name in self.names:
            if name in post.message:
                self.res[name]['in text count'] += 1
                # TODO: we need to walk across this list...
                # let's go back into the scraper and make sure that it gets all
                # of the info that there is to get on its first pass
                self.res[name]['in text likes'] += self._update_likes(post)

    def _update_in_comments_count(self, post):
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
        for name in post.likes:
            self._inc(name, 'likes given')
        return len(post.likes)

    def _update(self, post):
        self._update_in_text_count(post)
        self._update_in_comments_count(post)

    def tabulate(self):
        # let's go back and make posts into an object that holds things nicely.
        for post in self.posts:
            self._update(post)
        return self.res
