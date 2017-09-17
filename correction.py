import xml.etree.cElementTree as ET
from collections import defaultdict
import re

mapping_street = {'Ave': 'Avenue',
                  'AVE': 'Avenue',
                  'Ave.': 'Avenue',
                  'Blvd': 'Boulevard',
                  'Blvd.': 'Boulevard',
                  'Ct': 'Court',
                  'Dr': 'Drive',
                  'Dr.': 'Drive',
                  'Rd': 'Road',
                  'Rd.': 'Road',
                  'St': 'Street',
                  'St.': 'Street',
                  'Tr': 'Trail'}

mapping_dir = {'East': 'E',
               'N.E.': 'NE',
               'N.W.': 'NW',
               'N.W': 'NW',
               'North': 'N',
               'Northeast': 'NE',
               'Northwest': 'NW',
               'S.E': 'SE',
               'S.W.': 'SW',
               'South': 'S',
               'South-east': 'SE',
               'South-west': 'SW',
               'Southeast': 'SE',
               'Southwest': 'SW'}

street_format = re.compile(r'\b(\S+)\s(\S+)$')
postal_format = re.compile(r'[A-z]\d[A-z]\s\d[A-z]\d')


def replace_name(match):
    street, dir = match.groups()

    if street in mapping_street:
        street = mapping_street[street]

    if dir in mapping_dir:
        dir = mapping_dir[dir]

    return (street + " " + dir)


def update_addr(street_name):
    name = re.sub(street_format, replace_name, street_name)

    return name


def update_postal(postcode):
    no_space_format = re.compile(r'([A-z]\d[A-z])(\d[A-z]\d)')

    if not postal_format.match(postcode):
        m = no_space_format.match(postcode)

        if m:
            postcode = m.group(1) + " " + m.group(2)

    return postcode.upper()