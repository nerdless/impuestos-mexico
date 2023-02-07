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
from src.adapters.nominas_repository import MySQLNominasRepository
from src.adapters.isr_repository import MySQLISRsRepository
from src.domain.factura import Deducible
from src.settings import localconfig
import pandas as pd
import pudb
import requests
import io
from statistics import mode

my_rfc = os.environ['RFC']


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

def get_inflacion(date):
    post_infla = {'formatoCSV.x': '44',
              'series': 'SP1',
              'version': '2'}
    url = 'http://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarSeries'
    inflacion_cont = '\n'.join(str(requests.post(url, data=post_infla).content).split('\\r\\n')[12:])
    inflacion_data = pd.read_csv(io.StringIO(inflacion_cont), names=['fecha', 'inflacion'], na_values='N/E', skiprows=1)
    inflacion_data.dropna(inplace=True)
    inflacion_data['fecha'] = inflacion_data.fecha.map(lambda x: datetime.strptime(x, '%d/%m/%Y'))
    inflacion_data.set_index('fecha', inplace=True)
    inflacion_data['inflacion'] = inflacion_data.inflacion.astype(float)
    return inflacion_data.loc[date.replace(day=1)].iloc[0]

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
                concepto.regimen_id = int(int(input('Provide the regimen id o this concept: ')))
                # add deducible
                concepto_repo.add(Deducible(**concepto.dict()))
            deducible &= concepto.deducible
        if deducible:
            factura.deducible = True
            factura.regimen_id = mode([concepto.regimen_id or concepto in factura.conceptos])
            facturas_deducibles.append(factura)
    concepto_repo.close_connection()
    return facturas_deducibles

def generate_isr_servicios_report(facturas: List):
    print("#### ISR persona fisica report ########")
    data = pd.DataFrame([fact.dict() for fact in facturas])
    acreditable = data.loc[(data.emisor_rfc != my_rfc)&(data.tipo_comprobante.isin(['I', 'ingreso']))&(data.regimen_id == 1)]
    gastos =  acreditable.subtotal.sum()
    print(f"Total gastos: {gastos}")
    ingresos_facts = data.loc[(data.emisor_rfc == my_rfc)&(data.tipo_comprobante.isin(['I', 'ingreso']))&(data.regimen_id == 1)]
    ingresos =  ingresos_facts.subtotal.sum()
    print(f"Ingresos: {ingresos}")
    pudb.set_trace()

def generate_iva_mensual_report(facturas: List, no_finan_df):
    """ Generate IVA report"""
    print("#### IVA report ########")
    data = pd.DataFrame([fact.dict() for fact in facturas])
    my_revenue = data.loc[(data.emisor_rfc == my_rfc)&(data.tipo_comprobante.isin(['I', 'ingreso']))]
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
    
    print(f"Actividades grabadas al 16%: {round(my_total_revenue,0)}")
    print(f"IVA cobrado del periodo: {round(my_total_trasladado,0)}")
    print(f"IVA acreditable: {round(my_total_acreditable,0)}")
    iva_retenido = my_revenue.iva_retenido.sum()
    print(f"IVA retenido: {round(iva_retenido,0)}")
    print(f"Impuesto a cargo: {my_total_trasladado-my_total_acreditable-iva_retenido}")
    #pudb.set_trace()

def generate_isr_semestral_report(since_date, until_date, revenue_no_financiero, isr_info):
    no_finan_df = pd.DataFrame(revenue_no_financiero)
    no_finan_df['total'] = no_finan_df.abono + no_finan_df.interes - no_finan_df.comision - no_finan_df.recuperacion - no_finan_df.capital
    inflacion_inicial = get_inflacion(since_date)
    inflacion_final = get_inflacion(until_date)
    factor_inflacion = float(truncate((inflacion_final/inflacion_inicial) - 1, 4))
    print(f"Factor de inflacion: {factor_inflacion}, inicial: {inflacion_inicial}, final: {inflacion_final}")
    intereses_reales = []
    intereses_nominales = []
    ajustes_inflacion = []
    isr_retenido = []
    for institucion_id in no_finan_df.institucion_id.unique():
        saldo_diario = no_finan_df.loc[no_finan_df.institucion_id == institucion_id].set_index('fecha').resample('D').sum()
        saldo_diario['saldo'] = saldo_diario.total.cumsum()
        saldo_diario = saldo_diario.loc[saldo_diario.index >= since_date]
        saldo_promedio = saldo_diario.saldo.mean()
        interes_nominal = saldo_diario.interes.sum()
        print(f"interes nominal: {interes_nominal}")
        print(f"Saldo promedio {saldo_promedio}")
        ajuste = saldo_promedio * factor_inflacion
        print(f"ajuste inflacion: {ajuste}")
        interes_real = interes_nominal - ajuste
        print(f"interes real: {interes_real}")
        intereses_reales.append(interes_real)
        intereses_nominales.append(interes_nominal)
        ajustes_inflacion.append(ajuste)
    print(f"Ingresos percibidos: {sum(intereses_nominales)}")
    print(f"Deducciones autorizadas: {sum(ajustes_inflacion)}")
    print(f"Base gravable: {sum(intereses_reales)}")
    isr_level = isr_info.loc[(isr_info.limite_inferior <= interes_real)&(isr_info.limite_superior >= interes_real)].iloc[0]
    isr_tarifa = isr_level.cuota + (intereses_reales - isr_level.limite_inferior) * (isr_level.tasa/100)
    print(f"Impuesto conforme a tarifa: {isr_tarifa}")
    print(isr_info)
    print("Como declarar https://youtu.be/wjatcerwrtw?t=250")
    


def generate_isr_mensual_report(facturas: List, revenue_no_financiero):
    """ Generate isr report"""
    print("\n Ingresos del sistema no financiero.\n")
    to_delete_index = list(map(int, input("Select the indexes of facturas the are not deducibles in this month: ").split(',')))
    facturas_this_month = [factur for factur in facturas if facturas.index(factur) not in to_delete_index]
    facturas_df = pd.DataFrame([fact.dict() for fact in facturas_this_month])
    no_financiero_df = pd.DataFrame(revenue_no_financiero)
    print(f"Ingresos percibidos: {no_financiero_df.interes.sum()}")
    deduccines = 0
    utilidad = no_financiero_df.interes.sum() - deducciones
    print(f"Deducciones autorizadas: {deducciones}")
    print(len(facturas))

def generate_doit_mensual_report(facturas: List):
    """ Generate doit report"""
    print(len(facturas))

def generate_isr_anual_report(facturas: List, nominas: List, nofinanciero):
    """ Generate isr report"""
    print('################Sueldos, salarios y asimilados ##################')
    data = pd.DataFrame([nom.dict() for nom in nominas])
    ingreso_anual = data.groupby('emisor').percepciones.sum()
    ingreso_exento = ingreso_anual - data.groupby('emisor').total_gravado.sum()
    ingreso_exento.name = 'ingreso_exento'
    retenciones_isr = data.groupby('emisor').isr_retenido.sum()
    ingresos_table = pd.DataFrame([ingreso_anual, ingreso_exento, retenciones_isr]).T
    print(ingresos_table)
    print('#################Gastos Authorizados############################')
    print('##################Otros ingresos###############')
    no_finan_df = pd.DataFrame(nofinanciero)
    no_finan_df['total'] = no_finan_df.abono + no_finan_df.interes - no_finan_df.comision - no_finan_df.recuperacion - no_finan_df.capital
    pudb.set_trace()
    print(len(facturas))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ayuda para hacer una declaracion.')
    parser.add_argument('rfc', help="RFC de la entidad que declara", type=str)
    parser.add_argument('anio', help="Anio de la declaracion", type=int)
    parser.add_argument('--type', help='tipo de declaracion', type=str)
    parser.add_argument('--periodo', help='periodo a declarar', type=int)

    args = parser.parse_args()
    declaration_type = args.type

    print(f"declaracion {declaration_type} for {args.rfc}")
    if declaration_type == 'mensual':
        since_date = datetime(args.anio, args.periodo, 1)
        until_date = since_date + relativedelta(months=1)
    elif declaration_type == 'semestral':
        since_date = datetime(args.anio, max((args.periodo - 1) * 6, 1), 1)
        until_date = datetime(args.anio, args.periodo * 6, 1)
    else:
        since_date = datetime(args.anio, 1, 1)
        until_date = since_date + relativedelta(years=1)
    
    facturas_repo = MySQLFacturasRepository(logging.getLogger(), localconfig)
    # bring all facturas of the month with the concept
    facturas = facturas_repo.filter(rfc=args.rfc, since_date=since_date.date(), until_date=until_date.date())
    # facturas = facturas_repo.filter(rfc=args.rfc)
    facturas_repo.close_connection()

    nomina_repo = MySQLNominasRepository(logging.getLogger(), localconfig)
    nominas = nomina_repo.filter(rfc=args.rfc, since_date=since_date.date(), until_date=until_date.date())
    nomina_repo.close_connection()
    # Ensure all facturas are clasified between deducible and not deducible
    facturas = classify_facturas_deducibles(facturas)
    no_financiero_repo = MySQLNoFinancieroRepository(logging.getLogger(), localconfig)
    revenue_no_financiero = no_financiero_repo.filter(until_date=until_date.date())
    no_financiero_repo.close_connection()
    isr_repo = MySQLISRsRepository(logging.getLogger(), localconfig)
    isr_info = isr_repo.filter(until_date.year, declaration_type, args.periodo)
    isr_repo.close_connection()

    if declaration_type == 'mensual':
        no_finan_df = pd.DataFrame(revenue_no_financiero)
        no_finan_df = no_finan_df.loc[no_finan_df.fecha >= since_date]
        generate_iva_mensual_report(facturas, no_finan_df=no_finan_df)
        generate_isr_servicios_report(facturas)
        # generate_isr_mensual_report(facturas, revenue_no_financiero=revenue_no_financiero)
        generate_doit_mensual_report(facturas)
    elif declaration_type == 'semestral':
        generate_isr_semestral_report(since_date=since_date, until_date=until_date, revenue_no_financiero=revenue_no_financiero, isr_info=isr_info)
    else:
        generate_isr_anual_report(facturas, nominas, revenue_no_financiero)


# TODO: Separar arrendamiento, servicios profesionales, IVA y demas ingresos