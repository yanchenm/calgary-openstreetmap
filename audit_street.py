import xml.etree.cElementTree as ET
import re
from collections import defaultdict
import pprint

expected_dir = ['NW', 'NE', 'SW', 'SE', 'N', 'E', 'S', 'W']
expected_street = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square",
                   "Lane", "Road", "Trail", "Parkway", "Commons", "Terrace", "Heights", "Way",
                   "Bay", "Centre", "Circle", "Close", "Common", "Cove", "Crescent", "Gate",
                   "Grove", "Hill", "Landing", "Link", "Manor", "Mews", "Park", "Plaza",
                   "Rise", "Row", "View", "Villas", "Gardens", "Green"]

street_format = re.compile(r'\b(\S+)\s(\S+)$')
street_format_non_calgary = re.compile(r'\b\S+\.?$')


def audit_street_type(unexpected_street, unexpected_dir, street_name, city_name='Calgary'):
    if city_name == 'Calgary':
        m = street_format.search(street_name)

        if m:
            street_type = m.group(1)
            direction = m.group(2)

            if street_type not in expected_street:
                unexpected_street[street_type].add(street_name)

            if direction not in expected_dir:
                unexpected_dir[direction].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def is_city(elem):
    return (elem.attrib['k'] == "addr:city")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    unexpected_street = defaultdict(set)
    unexpected_dir = defaultdict(set)

    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            city = None
            for tag in elem.iter("tag"):
                if is_city(tag):
                    city = tag.attrib['v']
                if is_street_name(tag):
                    audit_street_type(unexpected_street, unexpected_dir, tag.attrib['v'], city)
    osm_file.close()
    return unexpected_street, unexpected_dir


us, ud = audit('calgary_canada.osm')
pprint.pprint(dict(us))
pprint.pprint(dict(ud))
