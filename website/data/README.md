GeoJSON Data
============

All data in this directory comes from the map provided by FoodShare at https://www.google.com/maps/d/u/0/viewer?mid=1JgYvjHJ9rTD1JfczjEn1HWdTizVlKsv9

The data is exported as KML and then converted to GeoJSON files using https://mygeodata.cloud/converter/

Then they are checked in here.

The GroceryDeliverArea class loads these files, turns the coordinates into a
set of polygons, and can then test whether a given address falls within the
bounds.
