#!/bin/bash
data_type=instantane

wget https://donnees.roulez-eco.fr/opendata/$data_type
unzip $data_type
rm $data_type

mv PrixCarburants* data.xml
