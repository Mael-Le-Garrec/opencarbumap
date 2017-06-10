#!/usr/bin/env python3

import datetime

base = "var addressPoints = ["
template = "[{}, {}, \"{}\", {{{}}}],\n"
template_fuel_begin = "var fuels = {"
template_fuel = "\"{}\": {{'min': {}, 'max': {}}},\n"
carbu_list = sorted(['Gazole', 'SP95', 'SP98', 'GPLc', 'E10', 'E85'])

from lxml import etree
import utm

output = open('carbus.js', 'w')
output.write(base + '\n')

tree = etree.parse("data.xml")
price_list = []
now = datetime.datetime.now()
two_weeks = datetime.timedelta(14)
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
            if datetime.datetime.strptime(child.get('maj'), "%Y-%m-%dT%H:%M:%S") + two_weeks > now:
                prices[child.get('nom')] = str(float(child.get('valeur')) / 1000)

        if child.tag == "rupture":
            ruptures.append(child.get('nom'))

        if child.tag == "ville":
            ville = child.text.title()

    carburants = []
    for name, price in list(prices.items()):
        carburants.append('"' + name + '":' + price)

    carburants = ', '.join(carburants)

    if latitude and longitude and prices:
        output.write(template.format(latitude, longitude, ville, carburants))
        price_list.append(prices)
output.write('];\n')

output.write(template_fuel_begin)
for i in carbu_list:
  tmp = [x for price in price_list for y, x in price.items() if y == i and float(x) > 0.01]
  output.write(template_fuel.format(i, min(tmp), max(tmp)))
output.write("};\n")

output.close()

