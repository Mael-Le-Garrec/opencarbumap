#!/usr/bin/env python3

import os
import os.path
from shapely.geometry import shape, Point
from datetime import datetime, timedelta
from lxml import etree
import json

import utm

class Data():
    fuel_names = sorted(['Gazole', 'SP95', 'SP98', 'GPLc', 'E10', 'E85'])

class JsData():
    def __init__(self):
        self.directory = "json"
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        
    def write_markers(self, addressPoints):
        handle = open(os.path.join(self.directory, "address_points.js"), "w")
        handle.write("var addressPoints = ")
        text = json.dumps(addressPoints, indent=2)
        handle.write(text)
        handle.close()

    def write_fuels(self, price_list):
        handle = open(os.path.join(self.directory, "fuels.js"), "w")
        handle.write("var fuels = ")
        fuels = {}

        for i in Data.fuel_names:
          tmp = [x for price in price_list for y, x in price.items() if y == i]
          fuels[i] = {'min': min(tmp), 'max': max(tmp)}

        handle.write(json.dumps(fuels, indent=2))
        handle.close()

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


def get_id(pdv):
    return pdv.get('id')


def check_price(prices, node):
    two_weeks = timedelta(14)
    now = datetime.now()
    pdv_date = datetime.strptime(node.get('maj'), "%Y-%m-%dT%H:%M:%S")
    
    if pdv_date + two_weeks > now:
        if node.get('valeur') == '1000': break
        price = float(node.get('valeur')) / 1000
        if price > 0.10:
            prices[node.get('nom')] = price


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

class Points():

    class Coords():
        def __init__(self, point, pdv_id):
            self.point = point
            self.pdv_id = pdv_id

    coords = []

    def __init__(self, filename='departements.json'):
        self.filename = filename
        self.open_data()


    def open_data(self):
        self.data = open(self.filename)
        self.data = json.load(self.data)[0]


    def add_point(self, point, pdv_id):
        self.coords.append(self.Coords(Point(*point), pdv_id))


    def get_averages(self):
        # check each polygon to see if it contains the point
        for i, feature in enumerate(self.data['features']):
            for coord in self.coords:
                polygon = shape(feature['geometry'])
                if polygon.contains(coord.point):
                    print('Point {} is inside {}'.format(coord.point, feature))

def parse_xml(filename):
    output = JsData()
    points = Points()

    tree = etree.parse(filename)
    addressPoints = []
    price_list = []

    for i, pdv in enumerate(tree.xpath('/pdv_liste/pdv')):
        addressPoint = []
        latitude, longitude = get_coords(pdv)
        pdv_id = get_id(pdv)
        fuels, city, sold_out = get_children(pdv)

        if latitude and longitude and fuels:
            addressPoint.append(latitude)
            addressPoint.append(longitude)
            addressPoint.append(city)
            addressPoint.append(fuels)
            addressPoints.append(addressPoint)
            price_list.append(fuels)

    output.write_markers(addressPoints)
    output.write_fuels(price_list)

    points.get_averages()


if __name__ == "__main__":
    parse_xml("data.xml")
