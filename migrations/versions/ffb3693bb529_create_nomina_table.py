"""create nomina table

Revision ID: ffb3693bb529
Revises: 78a05f2ddb27
Create Date: 2022-08-19 20:13:58.201388

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffb3693bb529'
down_revision = '78a05f2ddb27'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE nomina (
            id VARCHAR(250),
            fecha_inicial TIMESTAMP,
            fecha_final TIMESTAMP,
            fecha_pago TIMESTAMP,
            receptor VARCHAR(250),
            emisor VARCHAR(250),
            percepciones DOUBLE,
            deducciones DOUBLE,
            otros_pagos DOUBLE,
            total_gravado DOUBLE,
            total_retenido DOUBLE,
            isr_retenido DOUBLE,
            issm_retenido DOUBLE,
            PRIMARY KEY (id)
            )"""
    )


def downgrade() -> None:
    op.drop_table('nomina')
