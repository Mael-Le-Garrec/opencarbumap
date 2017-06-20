# opencarbumap

This is a map of french gas station. The color of markers depends of prices.
There is one layer per fuel.

Data come from french government open data: https://www.prix-carburants.gouv.fr/rubrique/opendata/.
This project uses the daily (*jour*) file.

## Example map

Here is an example map: http://hatrix.fr/opencarbumap/map.html

## Install

```bash
./download_data.sh
python3 read.py
firefox map.html
```

## Regular data download

Government's database is updated everyday at 5am. Thus, data can be downloaded
safely at 5:30am each day:

```
echo "30 5    * * *   hatrix  cd /path/to/dir/ && sh download_data.sh && python3 read.py" >> /etc/crontab
```

