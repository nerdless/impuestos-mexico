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

def response_to_daily_saldo(response):
    data = pd.read_excel(response.content, engine="custom_xlrd")
    data["saldo"] = data["Saldo de capital"].map(lambda x: float(x.replace(",", "").split(" ")[1]))
    data["recuperacion"] = 0
    data["fecha"] = pd.to_datetime(data["Fecha"], dayfirst=True)
    return data

def parse_movimientos(response):
    json_response = json.loads(response.text)
    data = pd.DataFrame()
    data["fecha"] = pd.to_datetime(data["Fecha"], dayfirst=True)
    data["total_comision"] = data["Débitos"].map(lambda x: float(x.replace(",","").split(" ")[1] if x != "-" else 0))
    data["total_interes"] = data["Créditos"].map(lambda x: float(x.replace(",","").split(" ")[1] if x != "-" else 0))
    comisiones_ops = ["Cargo por gestión de cuotas en mora", "Comisión de mantenimiento de cuenta", "Adhesión al fideicomiso: Comisión por inscipción"]
    cuotas = data.loc[data.Operación.map(lambda x: "Retorno por cuota" in x)]
    comisiones = data.loc[data.Operación.isin(comisiones_ops)]
    data = pd.concat([cuotas, comisiones])
    data["interes"] = data["total_interes"] / 1.16
    data["comision"] = data["total_comision"] / 1.16
    data["iva_interes"] = data["interes"] * 0.16
    data["iva_comision"] = data["comision"] * 0.16
    return data[["fecha", "interes", "iva_interes", "comision", "iva_comision"]]

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


    
    def crawl_saldo(self, start_date: datetime, final_date: datetime) -> pd.DataFrame:
        previous_data = start_date - relativedelta(day=1)
        url = f"https://www.afluenta.mx/data_table_call/_DT_LenderTaxReporting/filteryear-{previous_data.year}__filtermonth-{previous_data.month}__format-xls/dt/LenderTaxReporting"
        print("Getting ", url)
        response = self.webdriver.request("GET", url)
        daily_data = response_to_daily_saldo(response)
        while daily_data.fecha.max() < datetime(final_date.year, final_date.month, final_date.day):
            init_date = datetime(daily_data.fecha.max().year, daily_data.fecha.max().month, 1) + relativedelta(months=1)
            url = f"https://www.afluenta.mx/data_table_call/_DT_LenderTaxReporting/filteryear-{init_date.year}__filtermonth-{init_date.month}__format-xls/dt/LenderTaxReporting"
            print("Getting ", url)
            response = self.webdriver.request("GET", url)
            new_data = response_to_daily_saldo(response)
            daily_data = pd.concat([daily_data, new_data])
        daily_data["saldo_lagged"] = daily_data["saldo"].shift(1)
        daily_data["saldo_diff"] = daily_data["saldo"] - daily_data["saldo_lagged"]
        daily_data["abono"] = daily_data["saldo_diff"].map(lambda x: x if x > 0 else 0)
        daily_data["capital"] = daily_data["saldo_diff"].map(lambda x: abs(x) if x <= 0 else 0)
        daily_data = daily_data[["fecha", "abono", "capital", "recuperacion"]]
        return daily_data.loc[(daily_data.fecha >= start_date)&(daily_data.fecha <= final_date)]
    
    def crawl_movimientos(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # print(f"Getting page {page}")
        url = "https://doopla.mx/api/investor/movimientos"
        payload = self.payload.copy()
        payload["data[first_date]"] = (start_date - relativedelta(days=1)).date().isoformat()
        payload["data[last_date]"] = end_date.date().isoformat()
        response = request("POST", url, data=payload, headers=self.headers)
        json_response = json.loads(response.text)
        data = pd.DataFrame(json_response["movimientos"])
        min_id = int(data.id.min())
        id_delta = int(data.id.max()) - min_id
        print(min_id, id_delta)
        while int(data.u_catch_date.min()) > datetime.timestamp(start_date):
            payload["data[start]"] = str(min_id - id_delta)
            payload["data[end]"] = str(min_id)
            payload["type"] = "scroll"
            print("Getting new data", payload)
            response = request("POST", url, data=payload, headers=self.headers)
            json_response = json.loads(response.text)
            if json_response["m"] == 'No hay movimientos que mostrar':
                break
            new_data = pd.DataFrame(json_response["movimientos"])
            min_id = int(new_data.id.min())
            id_delta = int(new_data.id.max()) - min_id
            print(min_id, id_delta)
            data = pd.concat([data, new_data])
        return data


    def __crawl_impuestos(self, start_date: datetime, final_date: datetime) -> pd.DataFrame:
        saldo_df = self.crawl_saldo(start_date, final_date)
        movimientos = self.crawl_movimientos(start_date=start_date)
        daily_data = saldo_df.merge(movimientos, on="fecha")
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



