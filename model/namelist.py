import requests
import collections

BASE_URL = 'ldap.uchicago.edu'
PORT = '389'
ATTRIBUTES = 'ou=people,dc=uchicago,dc=edu'
SCOPE = 'sub'

def ldap_query(host, port, attributes, scope, filter_, extensions=''):
    fmt = 'http://{host}:{port}/DN?{attributes}?{scope}?{filter_}?{extensions}'
    query = fmt.format(host=host,
                       port=port,
                       attributes=attributes,
                       scope=scope,
                       filter_=filter_,
                       extensions=extensions)
    return requests.get(query)

def ldap_and(arg1, arg2):
    return _ldap_filter_join('&', arg1, arg2)

def ldap_or(arg1, arg2):
    return _ldap_filter_join('|', arg1, arg2)

def _ldap_filter_join(op, arg1, arg2):
    return "({}({})({})".format(op, arg1, arg2)

# def get_uidNumber(resp):
#     num_pat = re.compile(r'uidNumber: (\d+)')
#     return find_identfier(num_pat, resp)

# def get_uid(resp)
#     uid_pat = re.acompile(r'uid: (\w+)')
#     return find_identifier(uid_pat, resp)

def find_identifier(identifier, resp):
    pat = re.compile(r'{}: ([^)]+)')
    return pat.match(resp).groups(0)

Student = collections.namedtuple('Student',
                                 ('preferred_name', 'full_name', 'cnet'))

def ldap_scrape_all_students(host, port, attributes, scope):
    def students_uid_geq(uid):
        filter_ = ldap_and('uidNumber>={}'.format(uid),
                           ldap_or('eduPersonAffiliation=student',
                                   'eduPersonAffiliation=former_student'))
        return ldap_query(host, port, attributes, scope, filter_)
    
    resp = students_uid_geq(0)
    while resp:
        
        
    




