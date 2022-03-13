#!/bin/bash
curl --output stations.json https://z.overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%3B%28nwr%5B%22ref%3AFR%3Aprix-carburants%22%5D%28area%3A3601403916%29%3B%29%3Bout%20tags%20center%3B
