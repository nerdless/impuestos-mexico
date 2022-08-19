"""create facturas table

Revision ID: 78a05f2ddb27
Revises: 517e82138d13
Create Date: 2022-08-19 19:40:08.318900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78a05f2ddb27'
down_revision = '517e82138d13'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE facturas (
            id VARCHAR(250),
            fecha TIMESTAMP,
            receptor VARCHAR(250),
            emisor VARCHAR(250),
            concepto VARCHAR(250),
            tipo_comprobante VARCHAR(250),
            subtotal DOUBLE,
            total DOUBLE,
            iva_retenido DOUBLE,
            isr_retenido DOUBLE,
            iva_trasladado DOUBLE,
            isr_trasladado DOUBLE,
            ieps_trasladado DOUBLE,
            total_trasladado DOUBLE,
            deducible BOOLEAN,
            PRIMARY KEY (id)
            )"""
    )


def downgrade() -> None:
    op.drop_table('facturas')
