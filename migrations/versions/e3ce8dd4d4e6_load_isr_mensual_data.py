"""load isr mensual data

Revision ID: e3ce8dd4d4e6
Revises: 685c42aa7421
Create Date: 2022-08-18 20:33:19.268402

"""
from alembic import op
import sqlalchemy as sa
import os
from csv import reader



# revision identifiers, used by Alembic.
revision = 'e3ce8dd4d4e6'
down_revision = '685c42aa7421'
branch_labels = None
depends_on = None

data_path = "../../files/isr_mensual.csv"
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, data_path)

def upgrade() -> None:
    with open(filename, 'r') as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)
        # Iterate over each row in the csv using reader object
        rows = list(csv_reader)
        for row in rows[1:]:
            # row variable is a list that represents a row in csv
            query = f"""INSERT INTO isr_mensual (fecha, rango, limite_inferior, limite_superior, cuota, tasa)
                       VALUES ('{"','".join(row)}')"""
            op.execute(query)


def downgrade() -> None:
    pass
