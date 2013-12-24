import ldap3
import multiprocessing

SERVER_URL = 'ldap.uchicago.edu'
#PORT = '389'
DN = 'ou=people,dc=uchicago,dc=edu'
FILTER_PROPERTY_FMT = 'eduPersonAffiliation={}'
ATTRIBUTES = ['displayName', 'cn']
KEY_ON = 'uidNumber'
MAX_KEY = 10000000000

#SCOPE = 'sub'

class TooManyResponsesError(Exception):
    pass

def ldap_and(arg1, arg2):
    return _ldap_filter_join('&', arg1, arg2)

def ldap_or(arg1, arg2):
    return _ldap_filter_join('|', arg1, arg2)

def _ldap_filter_join(op, arg1, arg2):
    return "({}{}{})".format(op, arg1, arg2)

def make_ldap_filter(key, value, relation='='):
    return "({}{}{})".format(key, relation, value)

def ldap_scrape(server_url, dn, attributes_list, filters, key_on,
                max_key, min_key=0, port=389, chunk_size=10,
                pool_size=10):
    '''
    Scrapes an entire ldap server and returns a list of the requested
    attributes for each query. It requires at least one attribute that is
    numeric, so that it can break the work down into chunks and parallelize.
    '''

    conn = ldap3.Connection(
        ldap3.Server(server_url, port=port,
                     getInfo=ldap3.GET_ALL_INFO),
        clientStrategy=ldap3.STRATEGY_ASYNC_THREADED,)
    conn.open()

        
    #... and open up a new connection for each query to avoid a race
    def curried_query(filters_with_key):
        print('submitting query with filters: ', filters_with_key)
        res = conn.getResponse(
            conn.search(dn, filters_with_key, ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
                        attributes=attributes_list))

        # TODO: catch this and do something sensible
        # also rename
        if res[-1]['description'] != 'success':
            raise TooManyResponsesError
        # elif len(res) == 1:
        #     ret = None
        # else:
        #     ret = [[el['attributes'][a] for a in attributes] for el in res[:-1]]
        print('got response: ', res)
        return [[el['attributes'][a] for a in attributes] for el in res[:-1]]
        

    def build_filters_for_range(start_uid, end_uid):
        # print('building filters for: ', start_uid, ", ", end_uid)
        # fmt = '({key}{op}={val})'.format(key=key_on,
        #                                  op='{op}', val='{val}')
        # print(fmt)
        # lower_bound = fmt.format(op=">", val=start_uid)
        # upper_bound = fmt.format(op="<", val=end_uid)
        lower_bound = make_ldap_filter(key_on, start_uid, '>=')
        upper_bound = make_ldap_filter(key_on, end_uid, '<=')
        range_bounds = ldap_and(lower_bound, upper_bound)
        return ldap_and(filters, range_bounds) if filters else range_bounds

    # def unpack_chunk_tupe(chunk_tuple):
    #     return get_chunk(*chunk_tuple)
    
    def get_chunk(start_uid, end_uid):
        print('getting range from ', start_uid, 'to ', end_uid)
        return curried_query(build_filters_for_range(start_uid, end_uid))

    chunks = [(i*chunk_size, (i+1)*chunk_size)
              for i in range(min_key, (max_key // chunk_size) + 1)]

    print('chunks: ', chunks)

    if pool_size:
        with multiprocessing.Pool(pool_size) as pool:
            cnets = pool.map(get_chunk, chunks)
    else:
        cnets = map(lambda x: get_chunk(*x), chunks)

    tmp = cnets
    print('got :', list(cnets))
    
    # get rid of None responses
    return [c for c in cnets if c]

def scrape_uchicago():
    get_filter = lambda x: FILTER_PROPERTY_FMT.format(x)
    filters = ldap_or(get_filter('student'), get_filter('former_student'))

    return ldap_scrape(SERVER_URL, DN, ATTRIBUTES, filters, KEY_ON, MAX_KEY,
                       pool_size=1)
    
                      
