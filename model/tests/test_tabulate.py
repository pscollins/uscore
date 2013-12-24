import unittest
import pickle
from uscore.model import tabulate, scraper

# Expected output:

# 'in text count' is 1 for Stephen Landry, 0 otherwise
# 'in text likes' is 10 for Stephen Landry, 0 otherwise
# 'in comments count unique' is 1 for Stephen Landry, 0 otherwise
# 'in comments count gross' is 1 for Stephen Landry, 0 otherwise
# 'in comments likes' is 0 for everyone
# 'likes given' is

class TestTabulate(unittest.TestCase):
    PICKLED_POSTS = 'test_posts.json'
    NAME_LIST = 'test_names.txt'

    @classmethod
    def setUpClass(cls):
        with open(cls.PICKLED_POSTS, 'r') as f:
            posts = scraper.PostFactory.posts_from_file(f)
        with open(cls.NAME_LIST, 'r') as f:
            name_list = [l.strip() for l in f
                         if (l.strip() and not '#' in l)]
            # for line in f:
            #     print(line)
            #     if line.strip() and (not '#' in line):
            #         print('line ', line, 'is good')
            #         name_list += line.strip()
        
        # print(posts)
        cls.tabulator = tabulate.Tabulator(posts, name_list)
        cls.tabulator.tabulate()

    def test_tabulator__init__(self):
        for name in self.tabulator.names:
            self.assertIn(name, self.tabulator.res.keys())
        
    def test_tabulator_in_text(self):
        for name in self.tabulator.names:
            if name != 'Stephen Landry':
                self.assertEqual(self.tabulator.res[name]['in text count'], 0)
                self.assertEqual(self.tabulator.res[name]['in text likes'], 0)
            else:
                self.assertEqual(
                    self.tabulator.res['Stephen Landry']['in text count'], 1)
                self.assertEqual(
                    self.tabulator.res['Stephen Landry']['in text likes'], 10)

    def test_tabulate(self):
        self.tabulator.tabulate()

        # we test each one in a separate loop
        # so that later on we can refactor if need be


        for name in self.tabulator.names:
            to_test = self.tabulator.res[name]
            # print('to_test: ', to_test)
            if name != 'Stephen Landry':
                self.assertEqual(to_test['in comments count unique'], 0)
                self.assertEqual(to_test['in comments count gross'], 0)
            else:
                self.assertEqual(to_test['in comments count unique'], 1)
                self.assertEqual(to_test['in comments count gross'], 1)

        for name in self.tabulator.names:
            self.assertEqual(self.tabulator.res[name]['in comments likes'], 0)

        commentors = {
            "Alex Hayden DiLalla":1,
            "Alex McDonough":1,
            "Giovanni Vasko":2,
            "Kiran Misra":1,
            "Leilani Douglas":1,
            "MJ Chen":1,
            "Rajay Lee":1,
            "Stephanie Grach":1,
            }

        for name in self.tabulator.names:
            to_test = self.tabulator.res[name]['comments given']
            self.assertEqual(to_test,
                             commentors[name] if name in commentors else 0)

        likers = {
            "Alex Obasuyi":1,
            "Ashley Seymour":1,
            "Breanna Sullivan":1,
            "Brendon Mulholland":4,
            "Christine Hessler":1,
            "Danielle Doerr":1,
            "David Alexander Tomblin":1,
            "Dhyana Taylor":1,
            "Domitille Colin":1,
            "Emiliano Skillay":2,
            "Gabe Valley":1,
            "Haben Ghebregergish":3,
            "Hannah Friedman":3,
            "Harry Gao":1,
            "Ian Bergman":1,
            "Jennifer Tintoc":1,
            "Katie La Porte":2,
            "Kiran Misra":1,
            "Laura Brooke":1,
            "Lauren Nelson":1,
            "Leah Ansel":1,
            "Leilani Douglas":1,
            "Lisa Bonsignore-Opp":1,
            "Lucia Lu":1,
            "MJ Chen":1,
            "Marina Rioux":1,
            "Martin Montoya-Olsson":1,
            "Maya Lewinsohn":1,
            "Michael Weller":1,
            "Nahime Aguirre":1,
            "Natalie Naculich":1,
            "Nataly Rios":1,
            "Rachel Herrup":2,
            "Rachel Hile-Broad":3,
            "Rajay Lee":1,
            "Ron Yehoshua":1,
            "Rutvik Joglekar":1,
            "Samantha Slaton":1,
            "Sophie Downes":1,
            "Stephanie Grach":1,
            "Zelda Mayer":1
            }
            
        for name in self.tabulator.names:
            to_test = self.tabulator.res[name]['likes given']
            self.assertEqual(to_test,
                             likers[name] if name in likers else 0)

        for name in self.tabulator.names:
            to_test = self.tabulator.res[name]['links given']
            self.assertEqual(to_test,
                             1 if (name == 'Kiran Misra') else 0)
        
    
    def test_unique_adder(self):
        adder = tabulate.UniqueAdder(
            {name:{'comments given':0} for name in self.tabulator.names},
            'comments given')

        for x in range(0, 5):
            adder.add('MJ Chen')
        
        # print('result: ', adder.res)
        for name in self.tabulator.names:
            to_test = adder.res[name]['comments given']
            self.assertEqual(to_test,
                             1 if (name == 'MJ Chen') else 0)

    
        


if __name__ == '__main__':
    unittest.main()

            

            
        
