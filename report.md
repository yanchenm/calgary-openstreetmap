# Calgary OpenStreetMap Case Study

You will choose any area of the world in https://www.openstreetmap.org and use data munging techniques, such as assessing the quality of the data for validity, accuracy, completeness, consistency and uniformity, to clean the OpenStreetMap data for a part of the world that you care about. Finally, you will choose either MongoDB or SQL as the data schema to complete your project.

## Dataset

The dataset to be explored in this case study is the OpenStreetMap data for the city of [Calgary, Alberta, Canada](https://en.wikipedia.org/wiki/Calgary) (my hometown) obtained from https://mapzen.com/data/metro-extracts/metro/calgary_canada/. 

![Calgary Dataset Area](http://i.imgur.com/TReVKQO.png)

## Exploring the Dataset

The first step taken in processing the dataset is to take a smaller, easier to work with sample. Using the [sample.py](sample.py) script to take every 30th element, the 181 MB dataset can be reduced down to a more manageable 6 MB for initial exploration. 

To get an initial idea of the type of data contained within the dataset, a manual search through the dataset reveals the types of data that we can then audit programmatically. In an attempt to uncover potential problems within the OpenStreetMap data, we will be auditing in particular streetname and postal code data (which stood out as an obvious area for exploration) using the Python scripts [audit_street.py](audit_street.py) and [audit_postal_code.py](audit_postal_code.py). 

## Problems in the Dataset
#### Inconsistency of Street Name Formats

One of the unique challenges with dealing with the Calgary OpenStreetMap data is the format of streetnames used within Calgary city limits. The city follows a quadrant layout with many streets utilizing a numericly-named grid system. The numbering of the streets radiates out from the city center with numbers getting larger the further away they are from the center. This, of course, means that numbers will be repeated (i.e. there will be a 14th Street east of the center and also west). This street system means that all street addresses in Calgary are required to identify the quadrant within which they lie (NW, NE, SE, SW).

One of the major problems that exists within this dataset is the inconsistent use of streetname formats - particularly in the inconsistent abbreviation of both street names and quadrant names. To help identify the specific problems, the following (simplified version of original) code will be used to audit the street names.

```python
street_format = re.compile(r'\b(\S+)\s(\S+)$')

def audit_street_type(unexpected_street, unexpected_dir, street_name):
    m = street_format.search(street_name)
    if m:
        street_type, direction = m.groups()
        
        if street_type not in expected_street:
            unexpected_street[street_type].add(street_name)

        if direction not in expected_dir:
            unexpected_dir[direction].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    unexpected_street = defaultdict(set)
    unexpected_dir = defaultdict(set)

    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(unexpected_street, unexpected_dir, tag.attrib['v'])
    osm_file.close()
    return unexpected_street, unexpected_dir
```

The output from this script, however, was a little unexpected. The script was designed to pull the last two parts of a streetname - the street type (Street, Avenue, etc.) and the quadrant (NW, NE, etc.) and check them against a list of expected values. However, I noticed in the output that street type mismatches were often mismatches of actual street names (i.e. the 'Main' part of 'Main Street') compared to street types.

I soon realized that the issue here was that the OpenStreetMap dataset also included many of the area surrounding Calgary, some of which followed the Calgary street-naming convention using quadrants (like Airdrie), and many that didn't (like Bragg Creek and Chestermere). From here, I tweaked by script to also check the city an address is located in and audit only those within the actual city.

```python
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
```

With now accurate output, the two most obvious issues were that street types were inconsistently abbreviated and quadrants were inconsistently expanded. The steps to be taken to correct these issues are:
 - Expand all street type abbreviations to their full names ('4th Ave.' into '4th Avenue')
 - Collapse all quadrant names into accepted format ('Northwest' into 'NW')

```python
# Map inconsistencies to expected values
mapping_street = {'Ave': 'Avenue',
                  'AVE': 'Avenue',
                  ...
                  }

mapping_dir = {'East': 'E',
               'N.E.': 'NE',
               ...
               }

# Format to pull street info
street_format = re.compile(r'\b(\S+)\s(\S+)$')

def replace_name(match):
    street, dir = match.groups()
    
    # Check if street has an error to be corrected
    if street in mapping_street:
        street = mapping_street[street]

    if dir in mapping_dir:
        dir = mapping_dir[dir]

    return (street + " " + dir)

def update_addr(street_name):
    name = re.sub(street_format, replace_name, street_name)

    return name
```

#### Inconsistency of Postal Code Representation

Another major problem with the OpenStreetMap data is the inconsistency of the representation of Canadian postal codes. Canadian postal codes follow a specific format - A1A 1A1 (where 'A' represents any uppercase letter and '1' represents a numeric digit). All postal codes in the province of Alberta must also begin with 'T'. The following script can help determine if all the postal code entries are consistent and/or accurate.

```python
expected_postal_format = re.compile(r'T\d[A-z]\s\d[A-z]\d')

def is_postcode(elem):
    return (elem.attrib['k'] == 'addr:postcode')

def check_postcode(unexpected_postcodes, postcode):
    m = expected_postal_format.match(postcode)

    if not m:
        unexpected_postcodes.add(postcode)

# Similar audit function used as the above example
```

From this audit, it can be seen that there are a few common issues with the postal code consistency. For the sake of consistency, the following corrections will be applied to the data:
 - Add a space between each three letter grouping if not already present ('T1X1L8' -> 'T1X 1L8')
 - Capitalize all letters ('t2a 7y7' -> 'T2A 7Y7')
 - Remove any non-alphanumeric characters ('T3K-5P4' -> 'T3K 5P4')

```python
postal_format = re.compile(r'[A-z]\d[A-z]\s\d[A-z]\d')

def update_postal(postcode):
    no_space_format = re.compile(r'([A-z]\d[A-z])\S?(\d[A-z]\d)')

    if not postal_format.match(postcode):
        m = no_space_format.match(postcode)

        if m:
            postcode = m.group(1) + " " + m.group(2)

    return postcode.upper()
```

## SQL Database Processing

After initial data wrangling and exploration, the data can then be loaded into an SQLite database by first processing the OSM data into CSV files before importing them into SQLite. Before each element is loaded into CSV, they will be checked to see if they contain any of the errors uncovered in the previous stage. Any errors will be updated before being entered into the database.

```python
if (type == "addr") and (key == "street"):
    tag_dict['value'] = correction.update_addr(value)
elif (type == "addr") and (key == "postcode"):
    tag_dict['value'] = correction.update_postal(value)
else:
    tag_dict['value'] = value
```

The full script for loading to the database can be seen at [load_data.py](load_data.py).

## Data Overview in SQL
#### File Sizes
```
calgary_canada.osm     181 MB
calgary.db             101 MB
nodes.csv               68 MB
nodes_tags.csv         3.0 MB
ways.csv               6.4 MB
ways_nodes.csv          25 MB
ways_tags.csv           13 MB
```

#### Number of Unique Users
```sql
sqlite> SELECT COUNT(*)
        FROM (SELECT DISTINCT uid FROM nodes UNION SELECT DISTINCT uid FROM WAYS) as sub;
```
1026

#### Number of Nodes
```sql
sqlite> SELECT COUNT(*) FROM nodes;
```
852498
#### Number of Ways
```sql
sqlite> SELECT COUNT(*) FROM ways;
```
110710

#### Types of Amenities
```sql
sqlite> CREATE VIEW combined as 
        SELECT id, key, value FROM nodes_tags UNION ALL SELECT id, key, value FROM ways_tags;
        
sqlite> SELECT value, COUNT(*) as number
        FROM combined
        WHERE key = 'amenity'
        GROUP BY value ORDER BY number DESC LIMIT 10;
```
```
parking              1848
restaurant           659
fast_food            637
bench                497
school               398
fuel                 287
waste_basket         261
cafe                 244
bank                 216
place_of_worship     173
```

#### Popular Supermarkets
```sql
sqlite> SELECT value, COUNT(*) as number
        FROM combined JOIN (SELECT DISTINCT id FROM combined WHERE value = 'supermarket') as sub
        ON combined.id = sub.id
        WHERE key = 'name'
        GROUP BY value ORDER BY number DESC LIMIT 5;
```
```
Safeway                      24
Sobeys                        8
M&M Food Market               6
No Frills                     6
Real Canadian Superstore      6
```

## Additional Improvements

If we expand the above query for supermarkets to return the top 10 values instead of only the top 5,
```sql
sqlite> SELECT value, COUNT(*) as number
        FROM combined JOIN (SELECT DISTINCT id FROM combined WHERE value = 'supermarket') as sub
        ON combined.id = sub.id
        WHERE key = 'name'
        GROUP BY value ORDER BY number DESC LIMIT 10;
```
```
Safeway                      24
Sobeys                        8
M&M Food Market               6
No Frills                     6
Real Canadian Superstore      6
Superstore                    4
Walmart Supercentre           3
Community Natural Foods       2
Planet Organic                2
Shoppers Drug Mart            2
```
we can see that there are several more issues within the data returned by this query. First, we can see an inconsistency in naming. Both 'Real Canadian Superstore' and 'Superstore' refer to the same chain of supermarkets, yet they appear in separate entries within this table. Secondly, there are certainly more Walmarts in the Calgary area than just 3 (there are more than that in just the area I live). This suggests to us that either a large portion of Calgary data is undocumented or they appear in tags other than the 'supermarket' one we queried.

Both of these issues suggest the need for some kind of standard in the entry of OpenStreetMap data, whether by users or from other services. All supermarkets should fall under one type of tag, as should other amenities. Additionally, there should possibly be some type of software checking that flags tags with similar values to be human-checked to determine if they should be combined.

If this system were to be implemented, it would vastly increase both the accuracy and ease of use of the dataset. It would make errors like the above one where the same entity is represented under multiple entries much easier to detect and correct. It would make searching for specific categories of nodes much more comprehensive and overall makes the data in the dataset more accessible for all users.

However, the biggest potential issue for this particular way of improving the data would be the fact that there isn't a way to perfectly programmatically check these parameters. While guidelines can be provided to users regarding categorization of data, they are only guidelines with no way of enforcement other than manually checking the dataset. Similarly, we can only flag similar values in the dataset programmatically - in order to do anything further with that, human intervention is once again required. All of this means that while these improvements would greatly improve the dataset, it would also depend on the willingness of the OpenStreetMap community to actually go through with it and would always still have an element of human error. 