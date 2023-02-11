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
# from presta_utils import exceded_verifier#, load_historic
from dateutil.relativedelta import relativedelta
import time
#https://askubuntu.com/questions/851401/where-to-find-geckodriver-needed-by-selenium-python-package
#https://stackoverflow.com/questions/5660956/is-there-any-way-to-start-with-a-post-request-using-selenium

def exceded_verifier(text: str) -> bool:
    evaluation_text = '500 movimientos. Para conocer movimientos anteriores filtra los datos por fecha'
    return evaluation_text in text

def scrape_days(webdriver, url, init_date, time_delta):
        end_date = init_date + time_delta
        payload = {'actFiltro': 'FiltroOn',
                    'fdesde': init_date.strftime('%d/%m/%Y'),
                    'fhasta': end_date.strftime('%d/%m/%Y'),
                    'tipoOperacion': '%'}
        print('Getting delta: ', init_date, end_date)
        time.sleep(2)
        response = webdriver.request('POST', url, data=payload)
        if response.status_code != 200:
            print('Algo malo pasó con la peticion')
            print(response.status_code)
            print(response.text)
            time_delta = relativedelta(days=int(time_delta.days/2.0))
            print(payload)
            print('volviendo a intentar con ', time_delta.days)
            time.sleep(2)
            result = scrape_days(webdriver, url, init_date, time_delta)
            response = result[0]
            time_delta = result[1]
        else:
            print('Exito! continuo con delta de ', time_delta.days)        
        return response, time_delta
    

def response_to_daily(response):
    data_raw = pd.read_html(response.text)
    data_clean = data_raw[0].loc[~data_raw[0]['Autorización'].isin(['Principal:', 'Moratorios:', 'Interes:', 'Impuesto Interes:', 'Impuesto Moratorios:', 'IVA Comisión Moratorios:'])]
    pagos_data = data_clean.loc[data_clean.Tipo == 'PAGOS']
    final_data = data_clean.loc[~(data_clean.Tipo == 'PAGOS')]
    final_data['Importe'] = final_data['Importe'].str.replace('$', '').str.replace(',', '').astype(float)

    for i in np.arange(1, len(pagos_data)):
        fecha = pagos_data.iloc[i - 1]['Fecha Operación']
        this_log = data_raw[i].copy()
        this_log.columns = ['Movimiento', 'Importe']
        this_log['Fecha Operación'] = fecha
        final_data = final_data.append(this_log)

    final_data['fecha'] = pd.to_datetime(final_data['Fecha Operación'], dayfirst=True)
    final_data = final_data.pivot_table(index='fecha', columns=['Movimiento'], values='Importe', aggfunc='sum')
    daily_data = final_data.resample('D').sum()
    daily_data = daily_data.rename(columns={'FONDEO': 'abono', 'RECUPERACION': 'recuperacion', 'Principal:': 'capital'})
    if 'recuperacion' not in daily_data.columns:
        daily_data['recuperacion'] = 0
    if 'abono' not in daily_data.columns:
        daily_data['abono'] = 0
    daily_data['interes'] = daily_data['Interes:'] + daily_data['Moratorios:']
    daily_data['iva_interes'] = daily_data['interes'] * 0.16
    daily_data['comision'] = (daily_data['interes']+daily_data['recuperacion']+daily_data['capital']) * 0.01
    daily_data['iva_comision'] = daily_data['comision'] * 0.16
    daily_data['institucion_id'] = 'prestadero'
    return daily_data[['institucion_id', 'abono', 'comision', 'iva_comision', 'interes', 'iva_interes', 'recuperacion', 'capital']][:-1]

   
def scrape_historic_data(init_date, final_date, webdriver, url, time_delta=None):
    time_delta = time_delta or relativedelta(days=15)
    init_date += relativedelta(days=1)
    result = scrape_days(webdriver, url, init_date, time_delta)
    daily_data = response_to_daily(result[0])
    while daily_data.index.max() < datetime(final_date.year, final_date.month, final_date.day):
        init_date = daily_data.index.max().date() + relativedelta(days=1)
        result = scrape_days(webdriver, url, init_date, time_delta)
        response = result[0]
        time_delta = result[1]
        new_daily = response_to_daily(response)
        daily_data = pd.concat([daily_data, new_daily])
    return daily_data


class PrestaderoCrawler:
    institucion_id = "prestadero"
    init_date = datetime(2015,1,1)
    def __init__(self) -> None:
        self.webdriver = Firefox()
        self.webdriver.get("https://prestadero.com/iniciar-sesion.php")
        input("Are you logged in? ")
        self.no_financiero_repo = MySQLNoFinancieroRepository(logging.getLogger(), localconfig)


    def crawl(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, save_data=True):
        if start_date is None:
            revenue_no_financiero = self.no_financiero_repo.filter(institucion_ids=[self.institucion_id])
            if revenue_no_financiero:
                start_date = revenue_no_financiero[-1]['fecha']
            else:
                start_date = self.init_date
        if end_date is None:
            end_date = datetime.now()- relativedelta(days=1)
        daily_data = scrape_historic_data(start_date, end_date, self.webdriver, "https://prestadero.com/historial.php")
        return daily_data.reset_index()
    
    def close_connection(self):
        self.no_financiero_repo.close_connection()

    def save_data(self, data):
        print("Saving crawled data")
        for row in data.iterrows():
            item = DayStatus(**row[1].to_dict())
            self.no_financiero_repo.add(item)
        print("The data have been stored")



