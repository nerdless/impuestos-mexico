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
    data = data.drop_duplicates("id")
    data["monto"] = data.monto.astype(float)
    abonos = data.loc[data.status == 'Inversión']
    comisiones = data.loc[data.deposit_reason == 'Comision']
    pagos = data.loc[~data.id.isin(abonos.id.tolist() + comisiones.id.tolist())]
    abonos["abono"] = abonos.monto
    comisiones["total_comision"] = comisiones.monto

    data = pd.concat([abonos, comisiones, pagos])
    data["recuperacion"] = 0
    data['fecha'] = pd.to_datetime(data['u_catch_date'],unit='s')
    data["interes"] = data["intereses"].astype(float)
    data["iva_interes"] = data["interes"] * 0.16
    data["capital"] = data["capital"].astype(float)
    data["comision"] = data["total_comision"] / 1.16
    data["iva_comision"] = data["comision"] * 0.16
    return data[["fecha", "interes", "iva_interes", "comision", "iva_comision", "abono", "capital", "recuperacion"]]

def random_typing_time(mean_time=0.27, range=0.05):
    return mean_time + (random.random()*range) - range/2



class DooplaCrawler:
    institucion_id = "doopla"
    init_date = datetime(2019,4,12)


    def interceptor(self, request):
        if request.url == "https://doopla.mx/api/investor/movimientos":
            print("updating bearer")
            self.bearer = request.headers.get_all('authorization')[0]
            encoded_body = request.body.decode()
            self.payload = {item.split("=")[0]:item.split("=")[1] for item in unquote(encoded_body).split("&")}
            for key in ["data[start]", "data[end]", "type"]:
                self.payload.pop(key)
            self.headers = {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest", "authorization": self.bearer}



    def __init__(self) -> None:
        self.webdriver = webdriver.Firefox()
        self.webdriver.get("https://doopla.mx/iniciar-sesion")
        time.sleep(5)
        for c in os.environ["DOOPLA_USER"]:
            self.webdriver.find_element("id", "txtEmail").send_keys(c)
            time.sleep(random_typing_time())
        self.webdriver.find_element("xpath", "//button").click()
        time.sleep(5)
        for c in os.environ["DOOPLA_PWD"]:
            self.webdriver.find_element("id", "pw").send_keys(c)
            time.sleep(random_typing_time())
        self.webdriver.find_element("xpath", "//button").click()
        input("Are you logged in? ")
        self.webdriver.find_element("xpath", "//a[@href='movimientos-cuenta-inversionista']").click()
        time.sleep(3)
        self.webdriver.request_interceptor = self.interceptor
        self.webdriver.find_element("id", "findMoves").click()
        self.no_financiero_repo = MySQLNoFinancieroRepository(logging.getLogger(), localconfig)


    
    def crawl_movimientos(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # print(f"Getting page {page}")
        url = "https://doopla.mx/api/investor/movimientos"
        payload = self.payload.copy()
        payload["data[first_date]"] = (start_date - relativedelta(days=1)).date().isoformat()
        payload["data[last_date]"] = end_date.date().isoformat()
        payload["type"] = "filter"
        response = request("POST", url, data=payload, headers=self.headers)
        json_response = json.loads(response.text)
        data = pd.DataFrame(json_response["movimientos"])
        min_id = data.id.astype(int).min()
        max_id = data.id.astype(int).max()
        print(min_id, data.catch_date.min(),  data.catch_date.max())
        while int(data.u_catch_date.min()) > datetime.timestamp(start_date):
            payload["data[start]"] = str(min_id)
            payload["data[end]"] = str(max_id)
            payload["type"] = "scroll"
            print("Getting new data", payload)
            response = request("POST", url, data=payload, headers=self.headers)
            json_response = json.loads(response.text)
            if json_response["m"] == 'No hay movimientos que mostrar':
                print("No hay movimientos que mostrar")
                break
            new_data = pd.DataFrame(json_response["movimientos"])
            min_id = new_data.id.astype(int).min()
            max_id = new_data.id.astype(int).max()
            print(min_id, data.catch_date.min(),  data.catch_date.max())
            data = pd.concat([data, new_data])
        return data


    def __crawl_impuestos(self, start_date: datetime, final_date: datetime) -> pd.DataFrame:
        movimientos = pd.DataFrame()
        date_range = pd.date_range(start_date, final_date, freq='M')
        date_range = [start_date] + list(date_range) + [final_date]
        for cursor in range(1, len(date_range)):
            new_movimientos = self.crawl_movimientos(start_date=date_range[cursor-1], end_date=date_range[cursor])
            movimientos = pd.concat([movimientos, new_movimientos])
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



