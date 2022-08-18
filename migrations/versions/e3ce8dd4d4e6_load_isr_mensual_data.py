"""load isr mensual data

Revision ID: e3ce8dd4d4e6
Revises: 685c42aa7421
Create Date: 2022-08-18 20:33:19.268402

"""
from alembic import op
import sqlalchemy as sa
import os



# revision identifiers, used by Alembic.
revision = 'e3ce8dd4d4e6'
down_revision = '685c42aa7421'
branch_labels = None
depends_on = None

data_path = "files/isr_mensual.csv"
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, data_path)

def upgrade() -> None:
    op.execute(f"""LOAD DATA INFILE '{filename}' 
                    INTO TABLE isr_mensual 
                    FIELDS TERMINATED BY ',' 
                    ENCLOSED BY '"'
                    LINES TERMINATED BY '\\n'
                    IGNORE 1 ROWS""")


def downgrade() -> None:
    pass
