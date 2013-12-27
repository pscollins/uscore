import multiprocessing
import itertools
import subprocess
import re
import json

from concurrent import futures

SERVER_URL = 'ldap.uchicago.edu'
#SERVER_URL = '128.135.249.239'
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
                port=389, base_str=''):
    '''
    Scrapes an entire ldap server and returns a list of the requested
    attributes for each query. 
    '''

    QUERY_FMT = \
      '{server_url}:{port}/{dn}?{attributes}?{scope}?{filters}'
    QUERY_PROC = 'curl'
    OPTS = ['-s']
    # TIMEOUT_OPT = ['-m 5']
    TIMEOUT_OPT = []
    
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
        opts = [QUERY_PROC, query_str] + OPTS + (TIMEOUT_OPT if timeout else [])
        while True:
            try:
                response = \
                  subprocess.check_output(opts).decode()
                entries = process_response(response, search_attributes)
                break
            except subprocess.CalledProcessError as e:
                print("got error ", e, "for ", query_str)
                
        # print('got response: ')
        return entries

    def build_key_filter(key_val, star=False):
        key_filter = make_ldap_filter(key_on, key_val + ('*' if star else ''))
        return ldap_and(filters, key_filter)
    
    wp = futures.ThreadPoolExecutor()
    def make_queries(base_key):
        # testing
        if len(base_key) > 2:
            return []
        print('making queries for: ', base_key)
        res = []
        to_test = 'abcdefghijklmnopqrstuvwxyz0123456789'
        for i in 'abcdefghijklmnopqrstuvwxyz0123456789':
            new_base = base_key + i
                unstarred = wp.submit(query, build_key_filter(new_base))
                starred = wp.submit(query, build_key_filter(new_base, True),
                                    True)
            unstarred_res = unstarred.result()
            if unstarred_res:
                res += unstarred_res
            starred_res = starred.result()
            if starred_res:
                if starred_res is RESPONSE_TIMEOUT or len(starred_res) > 10:
                    res += make_queries(new_base)
                else:
                    res += starred_res
        
        return res

    elements = make_queries(base_str)
    
    # print('got :', elements)
    

    return elements

# need to put this outside so it can be pickled
def curried_scrape(base):
    edu_filter = lambda x: make_ldap_filter('eduPersonPrimaryAffiliation', x)
    filters = ldap_or(edu_filter('student'), edu_filter('former_student'))

    return ldap_scrape(SERVER_URL, DN, ATTRIBUTES, filters,
                       KEY_ON, base_str=base)

def scrape_uchicago(procs):
    to_check = 'abcdefghijklmnopqrstuvwxyz0123456789'
    l = [''.join(el) for el in itertools.permutations(to_check*2, 2)]
    print(l)
    with multiprocessing.Pool(procs) as pool:
        results = pool.map(curried_scrape, l[:5])

    print('length: ', len(results))
    print("got: ", results)
    ret = [r for result in results for r in result]
    return ret
    
                      
if __name__ == '__main__':
    names = scrape_uchicago(5)
    print(names)
    print("got ", len(names), " names")
    # with open('ldap_scraped.json', 'w') as f:
    #     json.dump(names, f)
