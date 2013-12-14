import unittest
import scoreboard

class TestScoreboard(unittest.TestCase):
    
    def test_get_graph_from_env(self):
        # the 'facebook.GraphAPI' call internally doesn't do any work
        # -- it just sets variables. 
        gr = scoreboard.get_graph_from_env()

        # so we need to make some calls to check
        name = gr.get_object("195466193802264")['name']
        
        self.assertIs(name, 'Facebook Developers')

if __name__ == '__main__':
    unittest.main()
                
