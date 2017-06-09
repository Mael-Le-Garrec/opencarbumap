#!/bin/bash

wget https://donnees.roulez-eco.fr/opendata/jour
unzip jour
mv PrixCarburants* data.xml
