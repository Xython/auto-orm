from test_orm import *
from random import random
from pprint import pprint

s1 = Spirit(name='威严满满')
s2 = Spirit(name='稳重成熟')
s3 = Spirit(name='称职门卫')
s4 = Spirit(name='端茶送水')
spirits = [s1, s2, s3, s4]
sites = [Site() for each in range(13)]

session.add_all(spirits + sites)

for spirit in spirits:
    for site in sites:
        spirit.add_rel_with_site(site, score=random() * 100)

session.commit()


def monitor():
    print(Spirit.query.filter(Spirit.dbg_is_status_activated == 1).all())
    print(Site.query.filter(Spirit.dbg_is_status_activated == 1).all())


monitor()
for spirit in spirits:
    spirit.deactivate()
    session.commit()
    monitor()
