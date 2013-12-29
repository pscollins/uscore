import unittest
import json

from uscore.scripts import json_to_namelist

class TestJSONToNameList(unittest.TestCase):
    JSON_TEST_PATH='./data/short_ldap_names.json'

    @classmethod
    def setUpClass(cls):
        with open(cls.JSON_TEST_PATH, 'r') as f:
            cls.names = json.load(f)

    def test_join_on_keys(self):
        KEYS =  ['givenName', 'sn']
        f = lambda names: json_to_namelist.join_on_keys(names, KEYS, 'FOO')
        to_test = f(self.names)
        
        expected = ['AdamFOOAbramson',
                    'ArunFOOAbraham',
                    'AhmadFOOAbdul',
                    'AdilaFOOAbdulwahid']
        self.assertEqual(to_test, expected)

        missing_keys = self.names[:3] + \
          [{k:v for k, v in self.names[3].items() if k != 'sn'}]

        self.assertEqual(f(missing_keys), expected[:3])
    

if __name__ == '__main__':
    unittest.main()
