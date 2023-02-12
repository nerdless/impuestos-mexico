# This script should be run in a host computer with firefox with selenium and geckodriver install
from os import read
from time import time
from typing import Optional
from datetime import datetime
import logging
from seleniumrequests import Firefox 
from src.settings import localconfig
from src.domain.no_financiero import DayStatus
import pandas as pd
from src.adapters.no_financiero_repository import MySQLNoFinancieroRepository
import numpy as np
import datetime as dt
from dateutil.relativedelta import relativedelta
import time

def response_to_daily_saldo(response):
    data = pd.read_excel(response.content, engine="custom_xlrd")
    data["saldo"] = data["Saldo de capital"].map(lambda x: float(x.replace(",", "").split(" ")[1]))
    data["recuperacion"] = 0
    data["fecha"] = pd.to_datetime(data["Fecha"], dayfirst=True)
    return data

def parse_movimientos(response):
    data = pd.read_html(response.content.decode())[0]
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





class AfluentaCrawler:
    institucion_id = "afluenta"
    init_date = datetime(2019,4,10)
    def __init__(self) -> None:
        self.webdriver = Firefox()
        self.webdriver.get("https://www.afluenta.mx/mi_afluenta/ingresar")
        input("Are you logged in? ")
        self.no_financiero_repo = MySQLNoFinancieroRepository(logging.getLogger(), localconfig)

    def crawl_saldo(self, start_date: datetime, final_date: datetime) -> pd.DataFrame:
        previous_data = start_date - relativedelta(day=1)
        url = f"https://www.afluenta.mx/data_table_call/_DT_LenderTaxReporting/filteryear-{previous_data.year}__filtermonth-{previous_data.month}__format-xls/dt/LenderTaxReporting"
        response = self.webdriver.request("GET", url)
        daily_data = response_to_daily_saldo(response)
        while daily_data.fecha.max() < datetime(final_date.year, final_date.month, final_date.day):
            init_date = daily_data.fecha.max() + relativedelta(days=1)
            url = f"https://www.afluenta.mx/data_table_call/_DT_LenderTaxReporting/filteryear-{init_date.year}__filtermonth-{init_date.month}__format-xls/dt/LenderTaxReporting"
            response = self.webdriver.request("GET", url)
            new_data = response_to_daily_saldo(response)
            daily_data = pd.concat([daily_data, new_data])
        daily_data["saldo_lagged"] = daily_data["saldo"].shift(1)
        daily_data["saldo_diff"] = daily_data["saldo"] - daily_data["saldo_lagged"]
        daily_data["abono"] = daily_data["saldo_diff"].map(lambda x: x if x > 0 else 0)
        daily_data["capital"] = daily_data["saldo_diff"].map(lambda x: abs(x) if x <= 0 else 0)
        daily_data = daily_data[["fecha", "abono", "capital", "recuperacion"]]
        return daily_data.loc[(daily_data.fecha >= start_date)&(daily_data.fecha <= final_date)]
    
    def crawl_movimientos(self, start_date: datetime) -> pd.DataFrame:
        page= 1
        print(f"Getting page {page}")
        url = f"https://www.afluenta.mx/misc/data_table_call/dt/LenderAccountMovements/_DT_LenderAccountMovements/filterdateFrom-all__page-"
        response = self.webdriver.request("GET", url + str(page))
        daily_data = parse_movimientos(response)
        while daily_data.fecha.min() > start_date:
            page += 1
            print(f"Getting page {page}")
            response = self.webdriver.request("GET", url + str(page))
            daily_data = pd.concat([daily_data, parse_movimientos(response)])
        return daily_data.set_index("fecha").resample('D').sum().reset_index()


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



