#!/bin/bash

wget https://donnees.roulez-eco.fr/opendata/instantane
unzip jour
rm jour
mv PrixCarburants* data.xml
