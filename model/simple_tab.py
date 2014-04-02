import tabulate
import scraper
import json

from uscore.scripts.json_to_namelist import *

with open('../data/ldap_scraped.json') as f:
    names = apply_to_file(first_and_last_name, f)

with open('./ps_full.json') as f:
    ps = scraper.PostBuilder.posts_from_file(f)

tab = tabulate.Tabulator(ps, names)
results = tab.tabulate()

with open('tabbed_full.json') as f:
    json.dump(results)
