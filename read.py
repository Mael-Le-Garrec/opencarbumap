#!/usr/bin/env python3

from datetime import datetime, timedelta
from lxml import etree
import utm

class Data():
    fuel_names = sorted(['Gazole', 'SP95', 'SP98', 'GPLc', 'E10', 'E85'])


class Templates():
    base = "var addressPoints = ["
    marker = "[{}, {}, \"{}\", {{{}}}],\n"
    fuel_begin = "var fuels = {"
    fuel = "\"{}\": {{'min': {}, 'max': {}}},\n"


class JsData():
    marker_begin = False

    def __init__(self, filename="carbus.js"):
        self.filename = filename
        self.file = open(filename, 'w')
        

    def write_base(self):
        self.marker_begin = True
        self.file.write(Templates.base + '\n')


    def write_marker(self, latitude, longitude, city, fuel):
        if not self.marker_begin:
            self.write_base()

        text = Templates.marker.format(latitude, longitude, city, fuel)
        self.file.write(text)


    def close_markers(self):
        self.file.write('];\n')


    def write_fuels(self, price_list):
        self.file.write(Templates.fuel_begin)

        for i in Data.fuel_names:
          tmp = [x for price in price_list for y, x in price.items() if y == i]
          self.file.write(Templates.fuel.format(i, min(tmp), max(tmp)))

        self.file.write("};\n")


    def close(self):
        self.file.close()


def get_coords(pdv):
    try:
        latitude = float(pdv.get('latitude'))
        longitude = float(pdv.get('longitude'))

        # sometimes latitude and longitude are switch
        if latitude < longitude:
          latitude, longitude = longitude, latitude

        # sometimes coordinate are already in WGS84
        if latitude > 100 or latitude < -100:
          latitude = latitude / 100000
          longitude = longitude / 100000
    except:
        latitude, longitude = '', ''

    return latitude, longitude


def check_price(prices, node):
    two_weeks = timedelta(14)
    now = datetime.now()
    pdv_date = datetime.strptime(node.get('maj'), "%Y-%m-%dT%H:%M:%S")
    
    if pdv_date + two_weeks > now:
        price = float(node.get('valeur')) / 1000
        if price > 0.10:
            prices[node.get('nom')] = str(price)


def get_children(pdv):
    prices = {}
    sold_out = []
    city = ''

    for child in pdv.getchildren():
        if child.tag == "prix":
            check_price(prices, child)

        if child.tag == "rupture":
            sold_out.append(child.get('nom'))

        if child.tag == "ville":
            city = child.text.title()

    return prices, city, sold_out

def fuels_prices(prices):
    fuels = []
    for name, price in list(prices.items()):
        fuels.append('"' + name + '":' + price)

    fuels = ', '.join(fuels)

    return fuels

def parse_xml(filename):
    output = JsData()

    tree = etree.parse(filename)
    price_list = []

    for i, pdv in enumerate(tree.xpath('/pdv_liste/pdv')):
        latitude, longitude = get_coords(pdv)
        prices, city, sold_out = get_children(pdv)
        fuels = fuels_prices(prices)

        if latitude and longitude and prices:
            output.write_marker(latitude, longitude, city, fuels)
            price_list.append(prices)

    output.close_markers()
    output.write_fuels(price_list)
    output.close()


if __name__ == "__main__":
    parse_xml("data.xml")
