import unittest
import scraper
import subprocess

# sets environment variables
import keys

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
                
