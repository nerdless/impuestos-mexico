import argparse
from calendar import month
from datetime import date, datetime
import os
from typing import List
import logging
from dateutil.relativedelta import relativedelta
from src.adapters.concepto_repository import MySQLConceptosRepository
from src.adapters.facturas_repository import MySQLFacturasRepository
from src.adapters.no_financiero_repository import MySQLNoFinancieroRepository
from src.domain.factura import Deducible
from src.settings import localconfig
import pandas as pd
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
                concepto.deducible = bool(int(input('Is that concepto deducible?: ')))
                # add deducible
                concepto_repo.add(Deducible(**concepto.dict()))
            deducible &= concepto.deducible
        if deducible:
            facturas_deducibles.append(factura)
    concepto_repo.close_connection()
    return facturas_deducibles


def generate_iva_mensual_report(facturas: List, revenue_no_financiero):
    """ Generate iva report"""
    print(len(facturas))
    data = pd.DataFrame([fact.dict() for fact in facturas])
    my_revenue = data.loc[(data.emisor_rfc == my_rfc)&(data.tipo_comprobante.isin(['I', 'ingreso']))]
    no_finan_df = pd.DataFrame(revenue_no_financiero)
    factura_publico = int(input("Facturaste no financiero este mes?: "))
    if not bool(factura_publico):
        my_total_revenue = my_revenue.subtotal.sum() + no_finan_df.interes.sum()
        my_total_trasladado = my_revenue.iva_trasladado.sum() + no_finan_df.iva_interes.sum()
    else:
        my_total_revenue = my_revenue.subtotal.sum()
        my_total_trasladado = my_revenue.iva_trasladado.sum()
    acreditable = data.loc[(data.emisor_rfc != my_rfc)&(data.tipo_comprobante.isin(['I', 'ingreso']))]
    iva_acreditable = acreditable.iva_trasladado.sum()
    print('Emisores de acreditable: ')
    print(acreditable.emisor_nombre.unique().tolist())
    print('Instituciones de no financiero: ')
    print(no_finan_df.institucion_id.unique().tolist())
    factura_no_financiero = int(input("Te facturo el sistema no financiero?: "))
    if not bool(factura_no_financiero):
        my_total_acreditable = iva_acreditable + no_finan_df.iva_comision.sum()
    else:
        my_total_acreditable = iva_acreditable
    
    print(f"Actividades grabadas al 16%: {my_total_revenue}")
    print(f"IVA cobrado del periodo: {my_total_trasladado}")
    print(f"IVA acreditable: {my_total_acreditable}")
    iva_retenido = my_revenue.iva_retenido.sum()
    print(f"IVA retenido: {iva_retenido}")
    print(f"Impuesto a cargo: {my_total_trasladado-my_total_acreditable-iva_retenido}")


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
    # facturas = facturas_repo.filter(rfc=args.rfc)
    facturas_repo.close_connection()
    # Ensure all facturas are clasified between deducible and not deducible
    facturas = classify_facturas_deducibles(facturas)

    if declaration_type == 'mensual':
        revenue_no_financiero = None
        no_financiero_repo = MySQLNoFinancieroRepository(logging.getLogger(), localconfig)
        revenue_no_financiero = no_financiero_repo.filter(since_date=since_date.date(), until_date=until_date.date())
        no_financiero_repo.close_connection()
        generate_iva_mensual_report(facturas, revenue_no_financiero=revenue_no_financiero)
        generate_isr_mensual_report(facturas)
        generate_doit_mensual_report(facturas)
    else:
        generate_isr_anual_report(facturas)


