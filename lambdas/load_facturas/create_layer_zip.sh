#!/bin/bash
mkdir -p lambdas/load_facturas/layer/python/lib/python3.8/site-packages
pip3 install -r requirements.txt -t lambdas/load_facturas/layer/python/lib/python3.8/site-packages/
zip -r files/mysqlpackage.zip lambdas/load_facturas/layer/*
echo "lambda layer available at files/mysqlpackage.zip"