"""Authors repository for Mongo."""
from src.domain.factura import Concepto
from typing import Optional
from src.repositories.concepto_repository import AbstractConceptosRepository
import pymysql
from src.types.types import Localconfig


class MySQLConceptosRepository(AbstractConceptosRepository):
    """ConceptosRepository."""

    def __init__(self, logger, localconfig: Localconfig):
        """Constructor."""
        self.__localconfig = localconfig
        self.__logger = logger
        self.__conn = self.get_connection()

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

    def add(self, item: Concepto) -> Optional[Concepto]:
        """Create/update concepto."""
        query = f"UPDATE deducible SET deducible = {int(item.deducible)} WHERE emisor_rfc = '{item.emisor_rfc}' AND receptor_rfc = '{item.receptor_rfc}' AND descripcion = '{item.descripcion}'"
        self.__execute_query(query)
        query = f"UPDATE conceptos SET deducible = {int(item.deducible)} WHERE emisor_rfc = '{item.emisor_rfc}' AND receptor_rfc = '{item.receptor_rfc}' AND descripcion = '{item.descripcion}'"
        self.__execute_query(query)