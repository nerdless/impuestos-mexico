from  xmltodict import parse
from dateutil import parser
import pymysql
import logging
import urllib.parse
from boto3 import resource
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import os
import sys

def lowercase_processor(path, key, value):
    return key.lower(), value

import glob

facturas_files = glob.glob('files/*.xml')
facturas = []
for file in facturas_files:
    with open(file, 'r') as f:
        facturas.append(parse(f.read(), postprocessor=lowercase_processor)['cfdi:comprobante'])

donatarias = ['GME920514V69']

iva_aliases = ['IVA', 'iva', '002']
isr_aliases = ['ISR', 'isr', '001']

print('Loading function')
s3_resource = resource('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rds_host = os.environ['host']
name = os.environ['user']
password = os.environ['password']
db_name = os.environ['db_name']

def get_connection():
    try:
    	conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    except pymysql.MySQLError as e:
        logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
        logger.error(e)
        sys.exit()
    return conn

def execute_query(conn, query):
    max_tries = 5
    try_number=0
    while not conn.open and try_number < max_tries:
        logger.info('Reconnecting to database...')
        conn = get_connection()
        try_number += 1
    if try_number > 0:
        logger.info('Now connected!')
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()

conn = get_connection()

class Concepto(BaseModel):
    """Concepto model."""
    factura_id: str
    emisor_rfc: str
    receptor_rfc: str
    emisor_nombre: str
    descripcion: Optional[str]
    deducible: Optional[bool]


class Factura(BaseModel):
    """Factura model."""
    id: str
    filepath: str
    fecha: datetime
    receptor_rfc: str
    receptor_nombre: str
    emisor_nombre: str
    emisor_rfc: str
    tipo_comprobante: str
    subtotal: float
    total: float
    iva_retenido: float
    isr_retenido: float
    iva_trasladado: float
    isr_trasladado: float
    conceptos: List[Concepto]
    deducible: Optional[bool]

class Nomina(BaseModel):
    """Nomina model."""
    id: str
    fecha_inicial: datetime
    fecha_final: datetime
    fecha_pago: datetime
    receptor: str
    emisor: str
    percepciones: float
    deducciones: float
    otros_pagos: float
    total_gravado: float
    total_retenido: float
    isr_retenido: float
    imss_retenido: float

def get_nomina(factura_info, filekey):
    id = filekey.split('/')[-1].replace('.xml', '')
    deducciones = factura_info['cfdi:complemento']['nomina12:nomina']['nomina12:deducciones']['nomina12:deduccion']
    importes = {deduccion[key].lower(): deduccion['@importe'] for deduccion in deducciones for key in deduccion if 'concepto' in key.lower()}
    isr_retenido = sum([float(importes[key]) for key in importes if 'isr' in key])
    imss_retenido = sum([float(importes[key]) for key in importes if 'imss' in key])

    return Nomina(id=id, fecha_inicial=parser.parse(factura_info['cfdi:complemento']['nomina12:nomina']['@fechainicialpago']),
                  fecha_final=parser.parse(factura_info['cfdi:complemento']['nomina12:nomina']['@fechafinalpago']),
                  fecha_pago=parser.parse(factura_info['cfdi:complemento']['nomina12:nomina']['@fechapago']),
                  receptor=factura_info['cfdi:receptor']['@rfc'], emisor=factura_info['cfdi:emisor']['@rfc'],
                  percepciones=float(factura_info['cfdi:complemento']['nomina12:nomina']['@totalpercepciones']),
                  deducciones=float(factura_info['cfdi:complemento']['nomina12:nomina']['@totaldeducciones']),
                  otros_pagos=float(factura_info['cfdi:complemento']['nomina12:nomina']['@totalotrospagos']),
                  total_gravado=float(factura_info['cfdi:complemento']['nomina12:nomina']['nomina12:percepciones']['@totalgravado']),
                  total_retenido=float(factura_info['cfdi:complemento']['nomina12:nomina']['nomina12:deducciones']['@totalimpuestosretenidos']),
                  isr_retenido=float(factura_info['cfdi:complemento']['nomina12:nomina']['nomina12:deducciones']['@totalimpuestosretenidos']),
                  imss_retenido=imss_retenido,
                  irs_retenido=isr_retenido
                  )

def get_donation(factura_info, filekey):
    factura_id = filekey.split('/')[-1].replace('.xml', '')
    conceptos_list = [concepto for concepto in factura_info['cfdi:conceptos']['cfdi:concepto']] if isinstance(factura_info['cfdi:conceptos']['cfdi:concepto'], list) else [factura_info['cfdi:conceptos']['cfdi:concepto']]
    conceptos_list = [{key.lower(): concepto[key] for key in concepto} for concepto in conceptos_list]
    conceptos = [Concepto(factura_id=factura_id, 
                          receptor_rfc=factura_info['cfdi:receptor']['@rfc'],
                          emisor_rfc=factura_info['cfdi:emisor']['@rfc'],
                          emisor_nombre=factura_info['cfdi:emisor']['@nombre'], 
                          descripcion=concepto['@descripcion']) for concepto in conceptos_list]

    factura_item = Factura(id=factura_id,
    filepath=filekey,
    fecha=parser.parse(factura_info.get('@fecha') or factura_info['@fecha']),
    receptor_rfc=factura_info['cfdi:receptor']['@rfc'],
    receptor_nombre=factura_info['cfdi:receptor']['@nombre'],
    emisor_rfc=factura_info['cfdi:emisor']['@rfc'],
    emisor_nombre=factura_info['cfdi:emisor']['@nombre'],
    tipo_comprobante=factura_info.get('@tipodecomprobante') or factura_info['@tipodecomprobante'],
    subtotal=float(factura_info.get('@subtotal') or factura_info['@subtotal']),
    total=float(factura_info.get('@total') or factura_info['@total']),
    isr_retenido=0,
    iva_retenido=0,
    isr_trasladado=0,
    iva_trasladado=0,
    conceptos=conceptos,
    deducible=None
    )
    return factura_item

def add_nomina(nomina: Nomina):
    values = '\',\''.join([str(value) for value in nomina.dict().values()])
    query = f"Insert ignore into nomina ({','.join(nomina.dict().keys())}) values ('{values}')"
    execute_query(conn, query)

def add_concept(concepto: Concepto):
    query = "Insert ignore into conceptos (factura_id, emisor_rfc, emisor_nombre, receptor_rfc, descripcion) values "
    query += f"('{concepto.factura_id}', '{concepto.emisor_rfc}', '{concepto.emisor_nombre}', '{concepto.receptor_rfc}',  '{concepto.descripcion}')"
    execute_query(conn, query)

def add_factura(factura: Factura):
    query = "Insert ignore into facturas (id, filepath, fecha, receptor_rfc, receptor_nombre, emisor_nombre, emisor_rfc, tipo_comprobante, subtotal, total, iva_retenido, isr_retenido, iva_trasladado, isr_trasladado) values "
    query += f"('{factura.id}', '{factura.filepath}', '{factura.fecha}', '{factura.receptor_rfc}', '{factura.receptor_nombre}', '{factura.emisor_nombre}', '{factura.emisor_rfc}', '{factura.tipo_comprobante}', '{factura.subtotal}', '{factura.total}', '{factura.iva_retenido}', '{factura.isr_retenido}', '{factura.iva_trasladado}', '{factura.isr_trasladado}')"
    execute_query(conn, query)

def get_factura(filekey, sourcebucketname):
    try:
        factura_file = s3_resource.Object(bucket_name=sourcebucketname, key=filekey)
        factura = factura_file.get()["Body"].read()
        factura_dict = parse(factura, postprocessor=lowercase_processor)
    except Exception as e:  
        logger.info(f'Error: Unable to load file: {e}')
        return None
    factura_info = factura_dict['cfdi:comprobante']
    factura_info['cfdi:receptor'] = {key.lower(): factura_info['cfdi:receptor'][key] for key in factura_info['cfdi:receptor']}
    factura_info['cfdi:emisor'] = {key.lower(): factura_info['cfdi:emisor'][key] for key in factura_info['cfdi:emisor']}

    if '@xmlns:nomina12' in factura_info: 
        return get_nomina(factura_info, filekey)

    if factura_info['cfdi:emisor']['@rfc'] in donatarias:
        logger.info("Emisor is a donataria")
        return get_donation(factura_info, filekey)
    
    if not factura_info.get('cfdi:impuestos'):
        return None

    factura_id = filekey.split('/')[-1].replace('.xml', '')
    impuestos_trasladados = factura_info.get('cfdi:impuestos', {}).get('cfdi:traslados', {}).get('cfdi:traslado', [])
    impuestos_trasladados = [impuestos_trasladados] if isinstance(impuestos_trasladados, dict) else impuestos_trasladados
    impuestos_trasladados = [{key.lower(): impuesto[key] for key in impuesto} for impuesto in impuestos_trasladados]
    iva_trasladado = sum([float(impuesto['@importe']) for impuesto in impuestos_trasladados if impuesto['@impuesto'] in iva_aliases])
    isr_trasladado = sum([float(impuesto['@importe']) for impuesto in impuestos_trasladados if impuesto['@impuesto'] in isr_aliases])

    impuestos_retenidos =  factura_info.get('cfdi:impuestos', {}).get('cfdi:retenciones', {}).get('cfdi:retencion', [])
    impuestos_retenidos = [impuestos_retenidos] if isinstance(impuestos_retenidos, dict) else impuestos_retenidos
    iva_retenido = sum([float(impuesto['@importe']) for impuesto in impuestos_retenidos if impuesto['@impuesto'] in iva_aliases])
    isr_retenido = sum([float(impuesto['@importe']) for impuesto in impuestos_retenidos if impuesto['@impuesto'] in isr_aliases])
    conceptos_list = [concepto for concepto in factura_info['cfdi:conceptos']['cfdi:concepto']] if isinstance(factura_info['cfdi:conceptos']['cfdi:concepto'], list) else [factura_info['cfdi:conceptos']['cfdi:concepto']]
    conceptos_list = [{key.lower(): concepto[key] for key in concepto} for concepto in conceptos_list]
    conceptos = [Concepto(factura_id=factura_id, 
                          receptor_rfc=factura_info['cfdi:receptor']['@rfc'],
                          emisor_rfc=factura_info['cfdi:emisor']['@rfc'],
                          emisor_nombre=factura_info['cfdi:emisor']['@nombre'], 
                          descripcion=concepto['@descripcion']) for concepto in conceptos_list]

    factura_item = Factura(id=factura_id,
    filepath=filekey,
    fecha=parser.parse(factura_info.get('@fecha') or factura_info['@fecha']),
    receptor_rfc=factura_info['cfdi:receptor']['@rfc'],
    receptor_nombre=factura_info['cfdi:receptor']['@nombre'],
    emisor_rfc=factura_info['cfdi:emisor']['@rfc'],
    emisor_nombre=factura_info['cfdi:emisor']['@nombre'],
    tipo_comprobante=factura_info.get('@tipodecomprobante') or factura_info['@tipodecomprobante'],
    subtotal=float(factura_info.get('@subtotal') or factura_info['@subtotal']),
    total=float(factura_info.get('@total') or factura_info['@total']),
    isr_retenido=isr_retenido,
    iva_retenido=iva_retenido,
    isr_trasladado=isr_trasladado,
    iva_trasladado=iva_trasladado,
    conceptos=conceptos,
    deducible=None
    )
    return factura_item


def lambda_handler(event, context):
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    logger.info(f'current file to save: {key}')
    factura = get_factura(key, bucket)
    if isinstance(factura, Factura):
        try:
            add_factura(factura)
        except Exception as e:
            conn.close()
            raise Exception(e)
        for concepto in factura.conceptos:
            try:
                add_concept(concepto)
            except Exception as e:
                conn.close()
                raise Exception(e)
    elif isinstance(factura, Nomina):
        try:
            add_nomina(factura)
        except Exception as e:
            conn.close()
            raise Exception(e)
    else:
        logger.info('No factura to add.')
    if conn.open:
        conn.close()
    return {
        'statusCode': 200
    }
