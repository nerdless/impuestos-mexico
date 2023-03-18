# This script should be run in a host computer with firefox with selenium and geckodriver install
from os import read
from time import time
import json
from typing import Optional
from requests import request
from datetime import datetime
from urllib.parse import unquote
import logging
from seleniumwire import webdriver
from src.settings import localconfig
from src.domain.no_financiero import DayStatus
import pandas as pd
from src.adapters.no_financiero_repository import MySQLNoFinancieroRepository
import numpy as np
import datetime as dt
from dateutil.relativedelta import relativedelta
import time
import os
import random



def parse_movimientos(data):
    data["monto"] = data.monto.astype(float)
    abonos = data.loc[data.tipo == 'Préstamo'].drop(["capital", "intereses"], 1)
    comisiones = data.loc[data.tipo == 'Comisión'].drop(["capital", "intereses"], 1)
    pagos = data.loc[data.tipo == 'Pago']
    abonos["abono"] = -1 * abonos.monto
    comisiones["total_comision"] = -1 * comisiones.monto
    pagos["interes"] = pagos["intereses"].astype(float) + pagos["moratorios"].astype(float)
    pagos["iva_interes"] = pagos["interes"] * 0.16

    data = pd.concat([abonos, comisiones, pagos])
    data["recuperacion"] = 0
    data["iva_interes"] = data["interes"] * 0.16
    data["capital"] = data["capital"].astype(float)
    data["comision"] = data["total_comision"] / 1.16
    data["iva_comision"] = data["comision"] * 0.16
    return data[["fecha", "interes", "iva_interes", "comision", "iva_comision", "abono", "capital", "recuperacion"]]

def random_typing_time(mean_time=0.27, range=0.05):
    return mean_time + (random.random()*range) - range/2



class YoteprestoCrawler:
    institucion_id = "yotepresto"
    init_date = datetime(2019,4,12)


    def interceptor(self, request):
        if request.url == "https://api.yotepresto.com/v2/investor/portfolio_investments" or request.url  == "https://api.yotepresto.com/v2/investor/movements":
            print("updating bearer")
            self.access_token = request.headers.get_all('access-token')[0]
            self.client = request.headers.get_all('client')[0]
            self.headers = {"access-token": self.access_token, "client": self.client, "uid": os.environ["YOTEPRESTO_USER"]}


    def __init__(self) -> None:
        self.webdriver = webdriver.Firefox()
        self.webdriver.get("https://app.yotepresto.com/sign-in/")
        time.sleep(5)
        for c in os.environ["YOTEPRESTO_USER"]:
            self.webdriver.find_element("id", "email").send_keys(c)
            time.sleep(random_typing_time())
        self.webdriver.find_element("xpath", "//button").click()
        time.sleep(5)
        self.webdriver.request_interceptor = self.interceptor
        for c in os.environ["YOTEPRESTO_PWD"]:
            self.webdriver.find_element("name", "password").send_keys(c)
            time.sleep(random_typing_time())
        self.webdriver.find_element("xpath", "//button").click()
        self.no_financiero_repo = MySQLNoFinancieroRepository(logging.getLogger(), localconfig)


    
    def crawl_movimientos(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        url = "https://api.yotepresto.com/v2/investor/movements"
        page = 1
        url += f"?min_date={start_date.isoformat()}&max_date={end_date.isoformat()}&"
        response = request("GET", url + f"page={page}", headers=self.headers)
        json_response = json.loads(response.text)
        if json_response.get('operation', 'no operation') == 'caching':
            time.sleep(5)
            return self.crawl_movimientos(start_date, end_date)
        
        data = pd.DataFrame(json_response["collection"])
        data["fecha"] = pd.to_datetime(data['fecha'], dayfirst=True)
        while data.fecha.min() > start_date:
            page += 1
            print(f"Getting page {page}")
            response = request("GET", url + f"page={page}", headers=self.headers)
            json_response = json.loads(response.text)
            if json_response["collection"] is None:
                break
            new_data = pd.DataFrame(json_response["collection"])
            new_data["fecha"] = pd.to_datetime(new_data['fecha'], dayfirst=True)
            data = pd.concat([data, new_data])
        return data


    def __crawl_impuestos(self, start_date: datetime, final_date: datetime) -> pd.DataFrame:
        movimientos = pd.DataFrame()
        movimientos = self.crawl_movimientos(start_date=start_date, end_date=final_date)
        daily_data = parse_movimientos(movimientos)
        daily_data = daily_data.set_index("fecha").resample('D').sum().reset_index()
        return daily_data.loc[(daily_data.fecha >= start_date)&(daily_data.fecha <= final_date)]

    def crawl(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, save_data=True):
        if start_date is None:
            revenue_no_financiero = self.no_financiero_repo.filter(institucion_ids=[self.institucion_id])
            if revenue_no_financiero:
                start_date = revenue_no_financiero[-1]['fecha'].date()
            else:
                start_date = self.init_date
        if end_date is None:
            end_date = datetime.now()- relativedelta(days=1)
        impuestos_data = self.__crawl_impuestos(start_date, end_date)
        impuestos_data["institucion_id"] = self.institucion_id
        return impuestos_data
    
    def close_connection(self):
        self.no_financiero_repo.close_connection()

    def save_data(self, data):
        print("Saving crawled data")
        for row in data.iterrows():
            item = DayStatus(**row[1].to_dict())
            self.no_financiero_repo.add(item)
        print("The data have been stored")



