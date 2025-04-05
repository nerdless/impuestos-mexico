import tabula
import pandas as pd
import argparse
from os.path import exists

FIBRAS = ['FIBRAHD', 'FIBRAMQ', 'FIBRAPL', 'FCFE', 'FPLUS']

def clean_df(df_list, fecha):
    expected_columns = {'Día', 'Folio de la', 'Tipo de Operación'}
    filtered_dfs = []
    for df in df_list:
        if not df.empty and set(df.columns).intersection(expected_columns):
            new_df = df[2:].dropna(how='all', axis=1)
            if len(new_df.columns) == 13:
                new_df.columns = ['dia', 'folio', 'tipo_operacion', 'emisora', 'serie', 'titulos', 'precio', 'interes', 'comision', 'impuesto', 'abono', 'cargo', 'moneda']
                filtered_dfs.append(new_df)
    data = pd.concat(filtered_dfs)
    data['fecha'] = data.dia.map(lambda x: pd.to_datetime(fecha.replace(day=int(x.split('/')[0]))))
    data = data.dropna(subset=['emisora'])
    return data



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', help='PDF file to parse')
    parser.add_argument('fecha', help='fecha del estado de cuenta')
    parser.add_argument('csv', help='CSV file to write')
    args = parser.parse_args()

    # Read PDF
    df = tabula.read_pdf(args.pdf, pages='all')

    fecha = pd.to_datetime(args.fecha)

    df = clean_df(df, fecha)

    if exists(args.csv):
        old_df = pd.read_csv(args.csv)
        old_df['fecha'] = pd.to_datetime(old_df['fecha'])
        df = pd.concat([old_df, df])
        df = df.drop_duplicates(subset=['folio']).sort_values('fecha')

    

    df.to_csv(args.csv, index=False)

    df = df[df.emisora.isin(FIBRAS)]
    import pdb; pdb.set_trace()