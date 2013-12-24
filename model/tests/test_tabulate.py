import unittest
import pickle
import uscore.models.tabulate

# Expected output:

# 'in text count' is 1 for Stephen Landry, 0 otherwise
# 'in text likes' is 10 for Stephen Landry, 0 otherwise
# 'in comments count unique' is 1 for Stephen Landry, 0 otherwise
# 'in comments count gross' is 1 for Stephen Landry, 0 otherwise
# 'in comments likes' is 0 for everyone
# 'likes given' is

class TestTabulator(unittest.TestCase):
    PICKLED_POSTS = 'test_posts.p'
    NAME_LIST = 'test_names.txt'

    def setUp(self):
        with open(PICKLED_POSTS, 'rb') as f:
            posts = pickle.load(f)
        with open(NAME_LIST, 'r') as f:
            name_list = []
            for line in f:
                if line.strip() and (not '#' in line):
                    name_list += line.strip()
        self.tabulator = Tabulator(posts, name_list)

    def test_tabulator__init__(self):
        for name in self.tabulator.names:
            self.assertIn(name, self.
        
