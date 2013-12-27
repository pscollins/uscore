import subprocess
import re

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


def process_response(resp_str, attributes):
    PATTERN  = r'\s*{attribute}: ([a-zA-z0-9 ]+)'
    responses = resp_str.split('\n\n\n')

    def matcher(attribute):
      return re.compile(PATTERN.format(attribute=attribute))

    def build_entry(r):
        return {a:matcher(a).search(r).group(1) for a in attributes
                       if matcher(a).search(r)}
    
    return [build_entry(r) for r in responses]

def get_entry_with_max(entries, key_on):
    return int(max([int(e[key_on]) for e in entries if key_on in e.keys()]))

def ldap_scrape(server_url, dn, attributes_list, filters, key_on,
                max_key=float('inf'), min_key=0, port=389):
    '''
    Scrapes an entire ldap server and returns a list of the requested
    attributes for each query. 
    '''

    QUERY_FMT = \
      '{server_url}:{port}/{dn}?{attributes}?{scope}?{filters}'
    QUERY_PROC = 'curl'
    
    search_attributes = attributes_list
    if key_on not in search_attributes:
        search_attributes.append(key_on)
                  
    def query(filters_with_key):
        query_str = QUERY_FMT.format(server_url=server_url, port=port, dn=dn,
                                     attributes=','.join(search_attributes),
                                     scope='sub', filters=filters_with_key)
        print('submitting query: ', query_str)
        response = \
          subprocess.check_output([QUERY_PROC, '-s', query_str]).decode()
        # print('got response: ')
        entries = process_response(response, search_attributes)
        max_key = get_entry_with_max(entries, key_on)
        return entries, max_key
        

    def build_filters_for_range(start_key_val):
        lower_bound = make_ldap_filter(key_on, start_key_val, '>=')
        return ldap_and(filters, lower_bound)

    
    def make_queries():
        res, key_val = query(build_filters_for_range(min_key))
        # print('res: ', res)
        print('key_val: ', key_val)
        while (key_val < max_key) and res:
            print('key_val: ', key_val, 'max_key: ', max_key)
            new_res, new_key_val = query(build_filters_for_range(key_val))
            if new_key_val == key_val:
                break
            else:
                res.extend(new_res)
                key_val = new_key_val
        return res

    elements = make_queries()
    
    # print('got :', elements)
    

    return elements

def scrape_uchicago():
    edu_filter = lambda x: make_ldap_filter('eduPersonPrimaryAffiliation', x)
    filters = ldap_or(edu_filter('student'), edu_filter('former_student'))
    
    return ldap_scrape(SERVER_URL, DN, ATTRIBUTES, filters, KEY_ON)
    
                      
if __name__ == '__main__':
    names = scrape_uchicago()
