import unittest
import scoreboard
import subprocess

import keys

class TestScoreboard(unittest.TestCase):
    ID_TO_TEST = "cocacola"
    def setUp(self):
        # make sure that our environment variables are set
        subprocess.call("./set-keys.sh")
        # initialize the scraper with the facebook devs page
        self.scraper = scoreboard.Scraper(self.ID_TO_TEST)

    def test_page_initialized(self):
        self.assertEqual(self.ID_TO_TEST, self.scraper.page.page_id)
        
    def test_get_graph_from_env(self):
        # the 'facebook.GraphAPI' call internally doesn't do any work
        # -- it just sets variables. 
        gr = self.scraper.page.graph

        # so we need to make some calls to check
        name = gr.get_object(self.ID_TO_TEST)['name']
        
        self.assertEqual(name, 'Coca-Cola')

    def test_query(self):
        self.assertRaises(self.scraper.page.admins().next(),
                          scoreboard.BadRequestError)
        self.assertRaises(self.scraper.page.tabs(),
                          scoreboard.EmptyResponseError)
        # this is going to break easily
        picture_url = self.scraper.page.picture("redirect=false").next()['data']['url']
        self.assertIn('profile-a', picture_url)

    def test_iterable_query(self):
        def f(query):
            ans = {}
            for el in query:
                ans += el
            return ans

        self.assertIn(
            f(self.scraper.page.picture("redirect=false")['data']['url']),
            'profile-a')
            
        
if __name__ == '__main__':
    unittest.main()
                
