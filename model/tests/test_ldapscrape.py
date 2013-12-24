import unittest

from uscore.model import ldapscrape

class TestLDAPScrape(unittest.TestCase):
    MY_UID_NUMBER = 77372
    MY_UID = 'pscollins'
    MY_DISPLAY_NAME = 'Patrick Collins'

    def test_get_me_single_process(self):
        attributes = ['uid', 'displayName', 'uidNumber']
        filter_ = ldapscrape.make_ldap_filter('uid', self.MY_UID)
        cnets = ldapscrape.ldap_scrape(ldapscrape.SERVER_URL,
                            ldapscrape.DN,
                            attributes,
                            filters=filter_,
                            key_on = 'uidNumber',
                            max_key = self.MY_UID_NUMBER + 10,
                            chunk_size=1000000,
                            pool_size=0)

        self.assertEqual(len(cnets), 1)
        self.assertEqual(cnets[0]['uid'], self.MY_UID)
        self.assertEqual(cnets[0]['displayName'], self.MY_DISPLAY_NAME)
        self.assertEqual(cnets[0]['uidNumber'], self.MY_UID_NUMBER)

        
if __name__ == '__main__':
    unittest.main()
