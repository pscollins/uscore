import unittest
#import scraper
import subprocess

from uscore.model import scraper

# sets environment variables
from uscore.config import keys



class TestPosts(unittest.TestCase):
    TEST_POSTS = \
      [scraper.Post(message="#5901\n\nI've always been somewhat grouchy about Christmas - I think it's a dumb holiday. But when you wished me merry Christmas, I smiled back at you and said merry Christmas back and I meant every word. The things I do for love. Ah well, I guess it's practically a secular holiday anyway.", comments=[{'from': {'name': 'MJ Chen', 'id': '1076410220'}, 'can_remove': False, 'id': '638016242925804_5479531', 'user_likes': False, 'like_count': 7, 'created_time': '2013-12-23T03:12:25+0000', 'message': '*Grinchy'}], likes=[{'id': '1080038948', 'name': 'Brendon Mulholland'}, {'id': '699351094', 'name': 'Haben Ghebregergish'}, {'id': '1419404635', 'name': 'Rachel Hile-Broad'}, {'id': '1244890517', 'name': 'Danielle Doerr'}, {'id': '630208520', 'name': 'Lucia Lu'}, {'id': '1467691928', 'name': 'David Alexander Tomblin'}, {'id': '100000477086810', 'name': 'Hannah Friedman'}]),
 scraper.Post(message="#5900\n\nStephen Landry, \n\nYour eyes are so bright\nYour brows are so fine\nWell, my question is: 'Hi,\nWould you want to be mine?'", comments=[{'from': {'name': 'Kiran Misra', 'id': '100002807604114'}, 'message_tags': [{'type': 'user', 'id': '1081550171', 'offset': 0, 'length': 14, 'name': 'Stephen Landry'}], 'can_remove': False, 'id': '638010522926376_5479489', 'user_likes': False, 'like_count': 0, 'created_time': '2013-12-23T02:58:58+0000', 'message': 'Stephen Landry'}, {'from': {'name': 'Alex Hayden DiLalla', 'id': '1288318785'}, 'can_remove': False, 'id': '638010522926376_5479495', 'user_likes': False, 'like_count': 3, 'created_time': '2013-12-23T03:00:45+0000', 'message': 'Love, The College Republicans.'}, {'from': {'name': 'Leilani Douglas', 'id': '100001420396036'}, 'can_remove': False, 'id': '638010522926376_5479567', 'user_likes': False, 'like_count': 0, 'created_time': '2013-12-23T03:31:01+0000', 'message': "Hahaha. Isn't this number 3?"}], likes=[{'id': '1176632697', 'name': 'Katie La Porte'}, {'id': '100000426422216', 'name': 'Lisa Bonsignore-Opp'}, {'id': '1080038948', 'name': 'Brendon Mulholland'}, {'id': '1322651454', 'name': 'Michael Weller'}, {'id': '700776010', 'name': 'Zelda Mayer'}, {'id': '1275153989', 'name': 'Natalie Naculich'}, {'id': '1629285456', 'name': 'Dhyana Taylor'}, {'id': '100001420396036', 'name': 'Leilani Douglas'}, {'id': '100000186184133', 'name': 'Marina Rioux'}, {'id': '100002807604114', 'name': 'Kiran Misra'}])]
    TEST_POSTS_LOCATION = 'scraper_test_tmp'
      
    def test_to_and_from_file(self):
        with open(self.TEST_POSTS_LOCATION, 'w') as f:
            scraper.PostBuilder.posts_to_file(self.TEST_POSTS, f)

        with open(self.TEST_POSTS_LOCATION, 'r') as f:
            ps = scraper.PostBuilder.posts_from_file(f)

        for old, new in zip(self.TEST_POSTS, ps):
            self.assertEqual(old, new)
            
            

            

class TestScraper(unittest.TestCase):
    ID = 'cocacola'
    NAME = 'Coca-Cola'
    PARTIAL_PICTURE = 'profile-a'
    def setUp(self):
        self.scraper = scraper.Scraper(self.ID)
    
    def test_page_initialized(self):
        self.assertEqual(self.ID, self.scraper.page.obj_id)
        
    def test_get_graph_from_env(self):
        # the 'facebook.GraphAPI' call internally doesn't do any work
        # -- it just sets variables. 
        gr = self.scraper.page.graph

        # so we need to make some calls to check
        name = gr.get_object(self.ID)['name']
        
        self.assertEqual(name, self.NAME)

    def test_query(self):
        picture_url = \
          self.scraper.page.picture().query(redirect='false')['data']['url']
        self.assertIn(self.PARTIAL_PICTURE, picture_url)
        
    def test_next(self):
        with self.assertRaises(scraper.BadRequestError):
            self.scraper.page.admins().next()
        with self.assertRaises(scraper.EmptyResponseError):
            r = self.scraper.page.tabs().next()
        picture_url = self.scraper.page.picture(redirect='false').next()['data']['url']
        self.assertIn(self.PARTIAL_PICTURE, picture_url)

    def test_iterable_query(self):
        def f(query):
            ans = {}
            for el in query:
                ans.update(el)
            return ans

        self.assertIn(
            self.PARTIAL_PICTURE,
            f(self.scraper.page.picture(redirect='false'))['data']['url'])


# TODO: now this is throwing an error because it says that the application
# isn't authorized... what the actual fuck?
    def test_update_scraper(self):
        posts = self.scraper.update_scoreboard(num_to_proc=3, limit='5')

        print(posts)
        print(posts[0])
        print(str(posts[0]))
        print("len:", len(posts))
        self.assertTrue(len(posts) > 10)

    
if __name__ == '__main__':
    unittest.main()
                
