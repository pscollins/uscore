import json


def join_on_keys(name_dicts, keys, sep=' '):
    '''
    Join the elements of a dictionary on the specified keys with the
    given separator, ignoring elements without the specified keys.
    '''
    key_set = set(keys)
    def has_keys(name_dict):
        '''True if the supplied keys are a subset of name_dict.keys()'''
        return (set(name_dict.keys()) & key_set) == key_set
    return [sep.join([el[key] for key in keys]) for el in
            filter(has_keys, name_dicts)]

def first_and_last_name(name_dicts):
    '''Join scraped LDAP names on givenName and sn'''
    return join_on_keys(name_dicts, ['givenName', 'sn'])


def apply_to_file(op, file_handle):
    '''Apply one of the operations to a jsonified file'''
    return op(json.load(file_handle))
    
    
