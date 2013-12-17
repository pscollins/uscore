import unittest
import scoreboard
import subprocess

import keys

class TestScoreboard(unittest.TestCase):
    ID = 'cocacola'
    NAME = 'Coca-Cola'
    PARTIAL_PICTURE = 'profile-a'
    def setUp(self):
        # make sure that our environment variables are set
        subprocess.call("./set-keys.sh")
        # initialize the scraper with the facebook devs page
        self.scraper = scoreboard.Scraper(self.ID)

    def test_page_initialized(self):
        self.assertEqual(self.ID, self.scraper.page.page_id)
        
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
        with self.assertRaises(scoreboard.BadRequestError):
            self.scraper.page.admins().next()
        with self.assertRaises(scoreboard.EmptyResponseError):
            r = self.scraper.page.tabs().next()
        picture_url = self.scraper.page.picture(redirect='false').next()['data']['url']
        self.assertIn(self.PARTIAL_PICTURE, picture_url)

    def test_iterable_query(self):
        def f(query):
            ans = ''
            for el in query:
                ans += el
            return ans

        self.assertIn(
            self.PARTIAL_PICTURE,
            f(self.scraper.page.picture(redirect='false').next()['data']['url'])
            )
            
        
if __name__ == '__main__':
    unittest.main()
                
