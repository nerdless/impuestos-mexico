"""Load regimenes

Revision ID: 5b97b7a1dc6d
Revises: e4bd427e565d
Create Date: 2023-01-22 21:16:06.012827

"""
from alembic import op
import sqlalchemy as sa
import os
from csv import reader


# revision identifiers, used by Alembic.
revision = '5b97b7a1dc6d'
down_revision = 'e4bd427e565d'
branch_labels = None
depends_on = None

data_path = "../../files/regimenes.csv"
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
            query = f"""INSERT INTO regimen_cat (id, description)
                       VALUES ('{"','".join(row)}')"""
            op.execute(query)


def downgrade() -> None:
    op.execute('DELETE FROM regimen_cat')