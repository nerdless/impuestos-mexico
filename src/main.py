import argparse
from calendar import month
from datetime import date, datetime
import os
from typing import List
import logging
from dateutil.relativedelta import relativedelta
from src.adapters.concepto_repository import MySQLConceptosRepository
from src.adapters.facturas_repository import MySQLFacturasRepository
from src.domain.factura import Deducible
from src.settings import localconfig
import pudb

my_rfc = os.environ['RFC']

def classify_facturas_deducibles(facturas: List):
    """ Classify facturas as deducibles."""
    # Look for conceptos not classified
    concepto_repo = MySQLConceptosRepository(logging.getLogger(), localconfig)
    facturas_deducibles = []
    for factura in facturas:
        deducible = True
        for concepto in factura.conceptos:
            if concepto.deducible is None:
                # ask for a classifycation
                print(concepto)
                concepto.deducible = bool(input('Is that concepto deducible?: '))
                # add deducible
                concepto_repo.add(Deducible(**concepto.dict()))
            deducible &= concepto.deducible
        if deducible:
            facturas_deducibles.append(factura)
    concepto_repo.close_connection()
    return facturas_deducibles
        

    # delete factura and concepto
    # add factura and concepto
    # Get facturas classified
    return facturas

def generate_iva_mensual_report(facturas: List):
    """ Generate iva report"""
    print(len(facturas))

def generate_isr_mensual_report(facturas: List):
    """ Generate isr report"""
    print(len(facturas))

def generate_doit_mensual_report(facturas: List):
    """ Generate doit report"""
    print(len(facturas))

def generate_isr_anual_report(facturas: List):
    """ Generate isr report"""
    print(len(facturas))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ayuda para hacer una declaracion.')
    parser.add_argument('rfc', help="RFC de la entidad que declara", type=str)
    parser.add_argument('anio', help="Anio de la declaracion", type=int)
    parser.add_argument('--mes', help='mes de la declaracion', type=int)

    args = parser.parse_args()
    declaration_type = 'mensual' if args.mes else 'anual'

    print(f"declaracion {declaration_type} for {args.rfc}")
    if declaration_type == 'mensual':
        since_date = datetime(args.anio, args.mes, 1)
        until_date = since_date + relativedelta(months=1)
    else:
        since_date = datetime(args.anio, 1, 1)
        until_date = since_date + relativedelta(years=1)
    
    facturas_repo = MySQLFacturasRepository(logging.getLogger(), localconfig)
    
    # bring all facturas of the month with the concept
    facturas = facturas_repo.filter(rfc=args.rfc, since_date=since_date.date(), until_date=until_date.date())
    facturas_repo.close_connection()
    # Ensure all facturas are clasified between deducible and not deducible
    facturas = classify_facturas_deducibles(facturas)

    if declaration_type == 'mensual':
        generate_iva_mensual_report(facturas)
        generate_isr_mensual_report(facturas)
        generate_doit_mensual_report(facturas)
    else:
        generate_isr_anual_report(facturas)


