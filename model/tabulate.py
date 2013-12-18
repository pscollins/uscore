'''Once we've gotten a big list of posts from the scraper, we process it with everything in this file'''


class Tabulator:
    def __init__(self, posts, name_list):
        self.posts = posts
        self.names = name_list
        self.res = {}
        for name in name_list:
            self._init_name(name)
            
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
            
    def _update_in_text_count(self, post):
        for name in self.names:
            if name in post.message:
                self.res[name]['in text count'] += 1
                # TODO: we need to walk across this list...
                # let's go back into the scraper and make sure that it gets all
                # of the info that there is to get on its first pass
                self.res[name]['in text likes'] += ...

    def _update_in_comments_count(self, post):
        has_unique_like = set()
        for comment in post.comments:
            commentor = comment['from']['name']
            linked = 
            self._check_name()
            self.res[

    def _update(self, post):
        self._update_in_text_count(post)
        self._update_in_comments_count(post)

    def tabulate(self):
        # let's go back and make posts into an object that holds things nicely.
        for post in self.posts:
            self._update(post)
