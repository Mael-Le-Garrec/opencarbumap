#!/usr/bin/env python3

import os
import sys
import os.path
from shapely.geometry import shape, Point
from datetime import datetime, timedelta
from lxml import etree
import json
import numpy as np
import logging

import utm

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class Data():
    fuel_names = sorted(['Gazole', 'SP95', 'SP98', 'GPLc', 'E10', 'E85'])

class JsData():
    def __init__(self):
        self.directory = "json"
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        
    def write_markers(self, addressPoints):
        handle = open(os.path.join(self.directory, "address_points.js"), "w")
        handle.write("var addressPoints=")
        text = json.dumps(addressPoints, separators=(',', ':'))
        handle.write(text)
        handle.close()

    def write_fuels(self, price_list):
        handle = open(os.path.join(self.directory, "fuels.js"), "w")
        handle.write("var fuels = ")
        fuels = {}

        for i in Data.fuel_names:
          tmp = [x for price in price_list for y, x in price.items() if y == i]
          fuels[i] = {'min': min(tmp), 'max': max(tmp)}

        handle.write(json.dumps(fuels, separators=(',', ':')))
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
        price = float(node.get('valeur')) / 1000
        if node.get('valeur') != '1000' and price > 0.10:
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
            city = child.text.title() if child.text else None # Sometimes ville is empty

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

    fuelPrices = reject_outliers_prices(addressPoints)
    give_quantile(addressPoints, fuelPrices)

    output.write_markers(addressPoints)
    output.write_fuels(price_list)

    points.get_averages()

def give_quantile(addressPoints, fuelPrices):
    quantiles = dict()
    for fuelId, prices in iter(fuelPrices.items()):
        quantiles[fuelId] = np.quantile(prices, [(n+1)/6 for n in range(5)])

    for address in addressPoints:
        address.append(dict())
        for fuelId, price in iter(address[3].items()):
            address[4][fuelId] = int(np.searchsorted(quantiles[fuelId], price))

def reject_outliers_prices(addressPoints, reject_factor=10):
    """ Filter outliers price from addressPoints using standard
        deviation and mean.

        reject condition: abs(price - mean) > reject_factor * std

        :param addressPoints: address point list
        :param reject_factor: used in reject condition
    """
    # extract all fuel price by fuel Id in a dict like
    # {'E10': [1.604, 1.602, ...], ...}
    fuelPrices = {}
    for address in addressPoints:
        for fuelId, price in iter(address[3].items()):
            if not fuelId in fuelPrices:
                fuelPrices[fuelId] = [price] # first entry
            else:
                fuelPrices[fuelId].append(price)

    # compute mean and standard deviation for all fuel Id
    fuelMeanStd = {}
    for fuelId, prices in iter(fuelPrices.items()):
        fuelMeanStd[fuelId] = {
            'mean': np.mean(prices),
            'std': np.std(prices)
        }

    # now we can filter previous result
    for address in addressPoints:
        for fuelId in list(address[3]):
            if abs(address[3][fuelId] - fuelMeanStd[fuelId]['mean']) > reject_factor * fuelMeanStd[fuelId]['std']:
                logging.info('rejecting fuel price: %s=%f (mean=%f, std=%f)', fuelId,
                             address[3][fuelId], fuelMeanStd[fuelId]['mean'], fuelMeanStd[fuelId]['std'])
                # remove the entry
                del address[3][fuelId]

    fuelPrices = {}
    for address in addressPoints:
        for fuelId, price in iter(address[3].items()):
            if not fuelId in fuelPrices:
                fuelPrices[fuelId] = [price] # first entry
            else:
                fuelPrices[fuelId].append(price)

    for fuelId, prices in iter(fuelPrices.items()):
                logging.info('%s prices: min: %f, max: %f', fuelId, np.min(prices), np.max(prices))

    return fuelPrices

if __name__ == "__main__":
    parse_xml("data.xml")
