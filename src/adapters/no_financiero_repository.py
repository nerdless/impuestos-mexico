"""Authors repository for Mongo."""
from datetime import date
from src.domain.factura import Factura
from src.domain.no_financiero import DayStatus
from typing import Any, Dict, List, Optional, TypedDict, cast
import pymysql
import logging
from src.repositories.no_financiero_repository import AbstractNoFinancieroRepository
from src.types.types import Localconfig


class MySQLNoFinancieroRepository(AbstractNoFinancieroRepository):
    """No financiero revenue Repository."""

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
        institucion_ids: Optional[List[str]] = None,
        since_date: Optional[date] = None,
        until_date: Optional[date] = None
    ) -> List[Dict]:
        """Filter no financiero."""
        query = f"SELECT * FROM diario_no_financiero"
        conditions = 0
        if institucion_ids:
            if conditions == 0:
                query += " WHERE "
            else:
                query += " AND "
            query += f"""institucion_id in ('{"','".join(institucion_ids)}')"""
            conditions += 1
        if since_date:
            if conditions == 0:
                query += " WHERE "
            else:
                query += " AND "
            query += f"""fecha >= '{since_date.isoformat()}'"""
            conditions += 1
        if until_date:
            if conditions == 0:
                query += " WHERE "
            else:
                query += " AND "
            query += f"""fecha <= '{until_date.isoformat()}'"""
            conditions += 1
        query += " ORDER BY fecha ASC"
        no_financiero = self.__execute_query(query)
        return no_financiero
    
    def add(self, item: DayStatus) -> Optional[DayStatus]:
        """Create/update Day status."""
        query = "Insert ignore into diario_no_financiero (fecha, institucion_id, abono, comision, iva_comision, interes, iva_interes, recuperacion, capital) values "
        query += f"('{item.fecha}',  '{item.institucion_id}', '{item.abono}', '{item.comision}', '{item.iva_comision}', '{item.interes}', '{item.iva_interes}', '{item.recuperacion}', '{item.capital}')"
        self.__execute_query(query)
        

    def delete(self, item: DayStatus) -> None:
        """Delete factura."""
        raise NotImplementedError