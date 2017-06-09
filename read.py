#!/usr/bin/env python3

base = "var addressPoints = ["
template = "  [{}, {}, {}],"

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

    print(latitude)
    print(longitude)

    prices = {}
    ruptures = []
    ville = ''
    for child in pdv.getchildren():
        if child.tag == "prix":
            prices[child.get('nom')] = child.get('valeur')
        
        if child.tag == "rupture":
            ruptures.append(child.get('nom'))

        if child.tag == "ville":
            ville = child.text

    #print('')
    #print('Ville : ' + ville)
    #print('  Carburants : ' + ', '.join([a + ' : ' + b for a,b in list(prices.items())]))
    #print('    Ruptures : ' + ', '.join(ruptures))

    if latitude and longitude:
        output.write(template.format(latitude, longitude, '') + '\n')

output.write('];\n')
output.close()


