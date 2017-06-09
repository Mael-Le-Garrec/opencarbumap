#!/bin/bash

wget https://donnees.roulez-eco.fr/opendata/jour
unzip jour
rm jour
mv PrixCarburants* data.xml
