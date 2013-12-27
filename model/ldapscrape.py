import subprocess
import re
import json

SERVER_URL = 'ldap.uchicago.edu'
#PORT = '389'
DN = 'ou=people,dc=uchicago,dc=edu'
FILTER_PROPERTY_FMT = 'eduPersonAffiliation={}'
ATTRIBUTES = ['displayName', 'cn', 'givenName', 'sn']
KEY_ON = 'uid'
MAX_KEY = 10000000000

#SCOPE = 'sub'

RESPONSE_TIMEOUT = object()

def ldap_and(arg1, arg2):
    return _ldap_filter_join('&', arg1, arg2)

def ldap_or(arg1, arg2):
    return _ldap_filter_join('|', arg1, arg2)

def _ldap_filter_join(op, arg1, arg2):
    return "({}{}{})".format(op, arg1, arg2)

def make_ldap_filter(key, value, relation='='):
    return "({}{}{})".format(key, relation, value)


def process_response(resp_str, attributes):
    PATTERN  = r'\s*{attribute}: ([a-zA-z0-9 ]+)'
    responses = resp_str.split('\n\n\n')

    def matcher(attribute):
        return re.compile(PATTERN.format(attribute=attribute))

    def build_entry(r):
        return {a:matcher(a).search(r).group(1) for a in attributes
                       if matcher(a).search(r)}
    
    return [build_entry(r) for r in responses]


def ldap_scrape(server_url, dn, attributes_list, filters, key_on='uid',
                port=389):
    '''
    Scrapes an entire ldap server and returns a list of the requested
    attributes for each query. 
    '''

    QUERY_FMT = \
      '{server_url}:{port}/{dn}?{attributes}?{scope}?{filters}'
    QUERY_PROC = 'curl'
    OPTS = ['-s']
    TIMEOUT_OPT = ['-m 3']
    
    search_attributes = attributes_list
    if key_on not in search_attributes:
        search_attributes.append(key_on)
                  
    def query(filters_with_key, timeout=False):
        query_str = QUERY_FMT.format(server_url=server_url, port=port, dn=dn,
                                     attributes=','.join(search_attributes),
                                     scope='sub', filters=filters_with_key)
        # print('submitting query: ', query_str)
        # we use a timeout to "short circuit" when we know we'll get
        # too many responses
        opts = OPTS + (TIMEOUT_OPT if timeout else [])
        try:
            response = \
              subprocess.check_output([QUERY_PROC, query_str] + opts).decode()
            entries = process_response(response, search_attributes)
        except subprocess.CalledProcessError as e:
            if e.returncode == 28:
                entries = RESPONSE_TIMEOUT
            else:
                raise e
                
        # print('got response: ')
        return entries

    def build_key_filter(key_val, star=False):
        key_filter = make_ldap_filter(key_on, key_val + ('*' if star else ''))
        return ldap_and(filters, key_filter)
    
    def make_queries(base_key):
        print('making queries for: ', base_key)
        res = []
        for i in 'abcdefghijklmnopqrstuvwxyz0123456789':
            new_base = base_key + i
            unstarred_res = query(build_key_filter(new_base))
            starred_res = query(build_key_filter(new_base, True), True)
            if unstarred_res:
                res += unstarred_res
            if starred_res:
                if starred_res is RESPONSE_TIMEOUT or len(starred_res) > 10:
                    res += make_queries(new_base)
                else:
                    res += starred_res
        
        return res

    elements = make_queries('')
    
    # print('got :', elements)
    

    return elements

def scrape_uchicago():
    edu_filter = lambda x: make_ldap_filter('eduPersonPrimaryAffiliation', x)
    filters = ldap_or(edu_filter('student'), edu_filter('former_student'))
    
    return ldap_scrape(SERVER_URL, DN, ATTRIBUTES, filters, KEY_ON)
    
                      
if __name__ == '__main__':
    names = scrape_uchicago()
    with open('ldap_scraped.json', 'w') as f:
        json.dump(names, f)
