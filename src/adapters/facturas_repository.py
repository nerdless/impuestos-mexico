"""Authors repository for Mongo."""
from datetime import date
from domain.factura import Concepto, Factura
from typing import Any, Dict, List, Optional, TypedDict, cast
from repositories.factura_repository import AbstractFacturasRepository
import pymysql
import logging
from src.types.types import Localconfig


class MySQLFacturasRepository(AbstractFacturasRepository):
    """FacturasRepository."""

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
        rfc: str,
        factura_ids: Optional[List[Factura]] = None,
        since_date: Optional[date] = None,
        until_date: Optional[date] = None
    ) -> List[Factura]:
        """Filter facturas."""
        query = f"SELECT * FROM facturas WHERE (emisor_rfc = '{rfc}' OR receptor_rfc = '{rfc}')"
        if factura_ids:
            query += f""" AND factura_id in ('{"','".join(factura_ids)}')"""
        if since_date:
            query += f""" AND fecha >= '{since_date.isoformat()}'"""
        if until_date:
            query += f""" AND fecha <= '{until_date.isoformat()}'"""
        facturas_db = self.__execute_query(query)
        facturas = []
        conceptos_query = "SELECT * FROM conceptos WHERE "
        for entry in facturas_db:
            query = conceptos_query + f"factura_id = '{entry['id']}'"
            entry['conceptos'] = [Concepto(**concepto) for concepto in self.__execute_query(query)]
            entry['factura_id'] = entry['id']
            facturas.append(Factura(**entry))
        # return [_cast_author(author) for author in authors]
        return facturas
    
    def add(self, item: Factura) -> Optional[Factura]:
        """Create/update factura."""
        raise NotImplementedError

    def delete(self, item: Factura) -> None:
        """Delete factura."""
        raise NotImplementedError