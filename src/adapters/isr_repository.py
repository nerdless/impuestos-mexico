"""Authors repository for Mongo."""
from datetime import date
from pandas import DataFrame
from typing import Any, Dict, List, Optional, TypedDict, cast
from repositories.isr_tablas_repository import AbstractISRsRepository
import pymysql
import logging
from src.types.types import Localconfig
import pandas as pd


class MySQLISRsRepository(AbstractISRsRepository):
    """ISRsRepository."""

    __db_name = "docs_with_authors_db"
    __authors_collection_name = "authors_st"

    def __init__(self, logger, localconfig: Localconfig):
        """Constructor."""
        self.__localconfig = localconfig
        self.__logger = logger
        self.__conn = self.get_connection()
        self.__logger.setLevel(logging.INFO)

    def get_connection(self):
        try:
            conn = pymysql.connect(host=self.__localconfig.host,
                                   user=self.__localconfig.user,
                                   passwd=self.__localconfig.password,
                                   db=self.__localconfig.db,
                                   cursorclass=pymysql.cursors.DictCursor,
                                   connect_timeout=5)
        except pymysql.MySQLError as e:
            self.__logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
            self.__logger.error(e)
        return conn
    
    def __execute_query(self, query):
        max_tries = 5
        try_number=0
        while not self.__conn.open and try_number < max_tries:
            self.__logger.info('Reconnecting to database...')
            self.__conn = self.__get_connection()
            try_number += 1
        if try_number > 0:
            self.__logger.info('Now connected!')
        with self.__conn.cursor() as cur:
            cur.execute(query)
            response = cur.fetchall()
            self.__conn.commit()
        return response
    
    def close_connection(self):
        if self.__conn.open:
            self.__conn.close()

    def filter(
        self,
        fecha: int,
        tipo: str,
        periodo: int
    ) -> pd.DataFrame:
        """Filter facturas."""
        query = f"SELECT * FROM isr_mensual WHERE fecha = '{fecha}'"
        isr_db = self.__execute_query(query)
        final_table = pd.DataFrame(isr_db)
        if tipo == 'anual':
            periodos_finales = 12
        if tipo == 'semestral':
            periodos_finales = 6 * periodo
        else:
            periodos_finales = periodo
        final_table['limite_superior'] = final_table['limite_superior'] * periodos_finales
        final_table['limite_inferior'] = final_table['limite_superior'].shift(1).fillna(0) + 0.01
        final_table.limite_superior.iloc[-1] = float("inf")
        final_table['cuota'] = final_table['cuota'] * periodos_finales
        return final_table