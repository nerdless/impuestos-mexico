"""create deducibles table

Revision ID: 517e82138d13
Revises: e3ce8dd4d4e6
Create Date: 2022-08-19 06:45:18.856080

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '517e82138d13'
down_revision = 'e3ce8dd4d4e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE deducibles (
            receptor VARCHAR(250),
            emisor VARCHAR(250),
            concepto VARCHAR(250),
            concepto_id VARCHAR(250),
            deducible BOOLEAN,
            PRIMARY KEY (receptor, emisor, concepto_id)
            )"""
    )


def downgrade() -> None:
    op.drop_table('deducibles')
