"""Create deducible cataloge

Revision ID: ab71c34d570e
Revises: ffb3693bb529
Create Date: 2022-10-14 05:51:12.627366

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab71c34d570e'
down_revision = 'ffb3693bb529'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE deducible (
            emisor_rfc VARCHAR(250),
            receptor_rfc VARCHAR(250),
            descripcion VARCHAR(250),
            deducible BOOLEAN,
            PRIMARY KEY (emisor_rfc, receptor_rfc, descripcion)
            )"""
    )


def downgrade() -> None:
    op.drop_table('deducible')
