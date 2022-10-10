#!/bin/bash
mkdir -p layer/python/lib/python3.8/site-packages
pip3 install -r requirements.txt -t layer/python/lib/python3.8/site-packages/
cd layer
zip -r mysqlpackage.zip *