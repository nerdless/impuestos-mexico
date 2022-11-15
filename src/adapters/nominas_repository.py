"""Authors repository for Mongo."""
from datetime import date
from domain.nomina import Nomina
from typing import Any, Dict, List, Optional, TypedDict, cast
from repositories.nomina_repository import AbstractNominasRepository
import pymysql
import logging
from src.types.types import Localconfig


class MySQLNominasRepository(AbstractNominasRepository):
    """NominasRepository."""

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
        rfc: str,
        ids: Optional[List[Nomina]] = None,
        since_date: Optional[date] = None,
        until_date: Optional[date] = None
    ) -> List[Nomina]:
        """Filter nominas."""
        query = f"SELECT * FROM nomina WHERE (receptor = '{rfc}')"
        if ids:
            query += f""" AND id in ('{"','".join(ids)}')"""
        if since_date:
            query += f""" AND fecha_pago >= '{since_date.isoformat()}'"""
        if until_date:
            query += f""" AND fecha_pago <= '{until_date.isoformat()}'"""
        nominas_db = self.__execute_query(query)
        # return [_cast_author(author) for author in authors]
        return [Nomina(**nomina) for nomina in nominas_db]
    
    def add(self, item: Nomina) -> Optional[Nomina]:
        """Create/update nomina."""
        raise NotImplementedError

    def delete(self, item: Nomina) -> None:
        """Delete nomina."""
        raise NotImplementedError