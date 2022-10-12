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

# import glob

# facturas_files = glob.glob('files/*.xml')
# facturas = []
# for file in facturas_files:
#     with open(file, 'r') as f:
#         facturas.append(parse(f.read())['cfdi:Comprobante'])



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


try:
	conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
	logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
	logger.error(e)
	sys.exit()

class Concepto(BaseModel):
    """Concepto model."""
    factura_id: str
    emisor_rfc: str
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


def add_concept(concepto: Concepto):
    query = "Insert into conceptos (factura_id, emisor_rfc, emisor_nombre, descripcion) values "
    query += f"('{concepto.factura_id}', '{concepto.emisor_rfc}', '{concepto.emisor_nombre}', '{concepto.descripcion}')"
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()

def add_factura(factura: Factura):
    query = "Insert into facturas (id, filepath, fecha, receptor_rfc, receptor_nombre, emisor_nombre, emisor_rfc, tipo_comprobante, subtotal, total, iva_retenido, isr_retenido, iva_trasladado, isr_trasladado) values "
    query += f"('{factura.id}', '{factura.filepath}', '{factura.fecha}', '{factura.receptor_rfc}', '{factura.receptor_nombre}', '{factura.emisor_nombre}', '{factura.emisor_rfc}', '{factura.tipo_comprobante}', '{factura.subtotal}', '{factura.total}', '{factura.iva_retenido}', '{factura.isr_retenido}', '{factura.iva_trasladado}', '{factura.isr_trasladado}')"
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()


def get_factura(filekey, sourcebucketname):
    try:
        factura_file = s3_resource.Object(bucket_name=sourcebucketname, key=filekey)
        factura = factura_file.get()["Body"].read()
        factura_dict = parse(factura)
    except Exception as e:  
        logger.info(f'Error: Unable to load file: {e}')
        return None
    factura_info = factura_dict['cfdi:Comprobante']

    if '@xmlns:nomina12' in factura_info or not factura_info.get('cfdi:Impuestos'):
        #TODO guadar en nomina
        return None

    factura_info['cfdi:Receptor'] = {key.lower(): factura_info['cfdi:Receptor'][key] for key in factura_info['cfdi:Receptor']}
    factura_info['cfdi:Emisor'] = {key.lower(): factura_info['cfdi:Emisor'][key] for key in factura_info['cfdi:Emisor']}
    factura_id = filekey.split('/')[-1].replace('.xml', '')
    impuestos_trasladados = factura_info.get('cfdi:Impuestos', {}).get('cfdi:Traslados', {}).get('cfdi:Traslado', [])
    impuestos_trasladados = [impuestos_trasladados] if isinstance(impuestos_trasladados, dict) else impuestos_trasladados
    impuestos_trasladados = [{key.lower(): impuesto[key] for key in impuesto} for impuesto in impuestos_trasladados]
    iva_trasladado = sum([float(impuesto['@importe']) for impuesto in impuestos_trasladados if impuesto['@impuesto'] in iva_aliases])
    isr_trasladado = sum([float(impuesto['@importe']) for impuesto in impuestos_trasladados if impuesto['@impuesto'] in isr_aliases])

    impuestos_retenidos =  factura_info.get('cfdi:Impuestos', {}).get('cfdi:Retenciones', {}).get('cfdi:Retencion', [])
    impuestos_retenidos = [impuestos_retenidos] if isinstance(impuestos_retenidos, dict) else impuestos_retenidos
    iva_retenido = sum([float(impuesto['@importe']) for impuesto in impuestos_retenidos if impuesto['@impuesto'] in iva_aliases])
    isr_retenido = sum([float(impuesto['@importe']) for impuesto in impuestos_retenidos if impuesto['@impuesto'] in isr_aliases])
    conceptos_list = [concepto for concepto in factura_info['cfdi:Conceptos']['cfdi:Concepto']] if isinstance(factura_info['cfdi:Conceptos']['cfdi:Concepto'], list) else [factura_info['cfdi:Conceptos']['cfdi:Concepto']]
    conceptos_list = [{key.lower(): concepto[key] for key in concepto} for concepto in conceptos_list]
    conceptos = [Concepto(factura_id=factura_id, receptor_rfc=factura_info['cfdi:Receptor']['@rfc'], receptor_nombre=factura_info['cfdi:Receptor']['@nombre'], emisor_nombre=factura_info['cfdi:Emisor']['@nombre'], emisor_rfc=factura_info['cfdi:Emisor']['@rfc'], descripcion=concepto['@descripcion']) for concepto in conceptos_list]

    factura_item = Factura(id=factura_id,
    filepath=filekey,
    fecha=parser.parse(factura_info.get('@fecha') or factura_info['@Fecha']),
    receptor_rfc=factura_info['cfdi:Receptor']['@rfc'],
    receptor_nombre=factura_info['cfdi:Receptor']['@nombre'],
    emisor_rfc=factura_info['cfdi:Emisor']['@rfc'],
    emisor_nombre=factura_info['cfdi:Emisor']['@nombre'],
    tipo_comprobante=factura_info.get('@tipoDeComprobante') or factura_info['@TipoDeComprobante'],
    subtotal=float(factura_info.get('@subTotal') or factura_info['@SubTotal']),
    total=float(factura_info.get('@total') or factura_info['@Total']),
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
    if factura:
        for concepto in factura.conceptos:
            add_concept(concepto)
        add_factura(factura)    
    return {
        'statusCode': 200
    }
