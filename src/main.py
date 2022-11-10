import argparse
import os
from typing import List

my_rfc = os.environ['RFC']

def classify_facturas_deducibles(facturas: List):
    """ Classify facturas as deducibles."""
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

    # bring all facturas of the month with the concept
    facturas = []

    # Ensure all facturas are clasified between deducible and not deducible
    facturas = classify_facturas_deducibles(facturas)

    if declaration_type == 'mensual':
        generate_iva_mensual_report(facturas)
        generate_isr_mensual_report(facturas)
        generate_doit_mensual_report(facturas)
    else:
        generate_isr_anual_report(facturas)


