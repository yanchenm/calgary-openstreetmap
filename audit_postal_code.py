import xml.etree.cElementTree as ET
import re

expected_postal_format = re.compile(r'[A-z]\d[A-z]\s\d[A-z]\d')


def is_postcode(elem):
    return (elem.attrib['k'] == 'addr:postcode')


def check_postcode(unexpected_postcodes, postcode):
    m = expected_postal_format.match(postcode)

    if not m:
        unexpected_postcodes.add(postcode)


def audit(filename):
    osmfile = open(filename, 'r')
    unexpected_postcodes = set()

    for event, elem in ET.iterparse(osmfile, events=("start",)):
        if elem.tag == 'node' or elem.tag == 'way':
            for tag in elem.iter('tag'):
                if is_postcode(tag):
                    check_postcode(unexpected_postcodes, tag.attrib['v'])

    osmfile.close()
    return unexpected_postcodes

print audit('calgary_canada.osm')