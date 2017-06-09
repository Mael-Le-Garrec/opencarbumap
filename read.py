#!/usr/bin/env python3

base = "var addressPoints = ["
template = "  [{}, {}, \"{}<br>{}\"],\n"

from lxml import etree
import utm

output = open('carbus.js', 'w')
output.write(base + '\n')

tree = etree.parse("data.xml")
for i, pdv in enumerate(tree.xpath('/pdv_liste/pdv')):
    try:
        latitude = float(pdv.get('latitude')) / 100000
        longitude = float(pdv.get('longitude')) / 100000
    except:
        latitude, longitude = '', ''

    prices = {}
    ruptures = []
    ville = ''
    for child in pdv.getchildren():
        if child.tag == "prix":
            prices[child.get('nom')] = str(float(child.get('valeur')) / 1000)
        
        if child.tag == "rupture":
            ruptures.append(child.get('nom'))

        if child.tag == "ville":
            ville = child.text
    
    carburants = '<br>'.join([a + ' : ' + b for a,b in list(prices.items())])

    if latitude and longitude and prices:
        output.write(template.format(latitude, longitude, ville, carburants))

output.write('];\n')
output.close()


