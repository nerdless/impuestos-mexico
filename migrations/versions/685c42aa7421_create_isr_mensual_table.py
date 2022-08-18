"""create isr mensual table

Revision ID: 685c42aa7421
Revises: 
Create Date: 2022-08-18 20:07:45.139724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '685c42aa7421'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE isr_mensual (
            fecha SMALLINT NOT NULL,
            rango TINYINT NOT NULL,
            limite_inferior DOUBLE,
            limite_superior DOUBLE,
            cuota DOUBLE,
            tasa DOUBLE,
            PRIMARY KEY (fecha, rango)
            )"""
    )


def downgrade() -> None:
    pass
