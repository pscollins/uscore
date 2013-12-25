import ldap3
import multiprocessing

SERVER_URL = 'ldap.uchicago.edu'
#PORT = '389'
DN = 'ou=people,dc=uchicago,dc=edu'
FILTER_PROPERTY_FMT = 'eduPersonAffiliation={}'
ATTRIBUTES = ['displayName', 'cn', 'givenName', 'sn']
KEY_ON = 'uidNumber'
MAX_KEY = 10000000000

#SCOPE = 'sub'

def ldap_and(arg1, arg2):
    return _ldap_filter_join('&', arg1, arg2)

def ldap_or(arg1, arg2):
    return _ldap_filter_join('|', arg1, arg2)

def _ldap_filter_join(op, arg1, arg2):
    return "({}{}{})".format(op, arg1, arg2)

def make_ldap_filter(key, value, relation='='):
    return "({}{}{})".format(key, relation, value)

def ldap_scrape(server_url, dn, attributes_list, filters, key_on,
                max_key=float('inf'), min_key=0, port=389):
    '''
    Scrapes an entire ldap server and returns a list of the requested
    attributes for each query. 
    '''

    conn = ldap3.Connection(
        ldap3.Server(server_url, port=port,
                     getInfo=ldap3.GET_ALL_INFO),
        clientStrategy=ldap3.STRATEGY_ASYNC_THREADED)
    conn.open()

    search_attributes = attributes_list
    if key_on not in search_attributes:
        search_attributes.append(key_on)
                  
    def query(filters_with_key):
        print('submitting query with filters: ', filters_with_key)
        res = conn.getResponse(
            conn.search(dn, filters_with_key, ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
                        attributes=search_attributes))
        print('got response: ', res)
        response_list = [{a:el['attributes'][a][0] for a in attributes_list}
                         for el in res[:-1]]
        # uidNumber gives us a list
        key_vals = [int(el['attributes'][key_on][0]) for el in res[:-1]]

        return response_list, max(key_vals)
        

    def build_filters_for_range(start_key_val):
        lower_bound = make_ldap_filter(key_on, start_key_val, '>=')
        return ldap_and(filters, lower_bound)

    
    def make_queries():
        res, key_val = query(build_filters_for_range(min_key))
        print('res: ', res)
        print('key_val: ', key_val)
        while (key_val < max_key) and res:
            print('key_val: ', key_val, 'max_key: ', max_key, 'res:', res)
            new_res, new_key_val = query(build_filters_for_range(key_val))
            if new_key_val == key_val:
                break
            else:
                res.append(new_res)
                key_val = new_key_val
        return res

    elements = make_queries()
    
    print('got :', elements)
    

    return elements

def scrape_uchicago():
    edu_filter = lambda x: make_ldap_filter('eduPersonPrimaryAffiliation', x)
    filters = ldap_or(edu_filter('student'), edu_filter('former_student'))
    
    return ldap_scrape(SERVER_URL, DN, ATTRIBUTES, filters, KEY_ON)
    
                      
