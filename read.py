#!/usr/bin/env python3

import os
import sys
import os.path
from datetime import datetime, timedelta
from lxml import etree
import json
import numpy as np
import logging

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
        prices[node.get('nom')] = float(node.get('valeur')) / 1000


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


def parse_xml(filename):
    output = JsData()

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

    output.write_markers(addressPoints)

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

if __name__ == "__main__":
    parse_xml("data.xml")
