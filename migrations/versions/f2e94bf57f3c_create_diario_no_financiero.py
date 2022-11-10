"""Create diario no financiero

Revision ID: f2e94bf57f3c
Revises: ab71c34d570e
Create Date: 2022-10-18 07:14:00.598140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2e94bf57f3c'
down_revision = 'ab71c34d570e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE diario_no_financiero (
            fecha TIMESTAMP,
            institucion_id VARCHAR(250),
            abono DOUBLE,
            comision DOUBLE,
            iva_comision DOUBLE,
            interes DOUBLE,
            iva_interes DOUBLE,
            recuperacion DOUBLE,  
            capital DOUBLE,
            PRIMARY KEY (fecha, institucion_id)
            )"""
    )


def downgrade() -> None:
    op.drop_table('diario_no_financiero')