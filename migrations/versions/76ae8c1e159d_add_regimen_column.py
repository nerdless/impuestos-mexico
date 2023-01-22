"""add regimen column

Revision ID: 76ae8c1e159d
Revises: 5b97b7a1dc6d
Create Date: 2023-01-22 21:24:59.054359

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76ae8c1e159d'
down_revision = '5b97b7a1dc6d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """ALTER TABLE conceptos 
        ADD COLUMN regimen_id MEDIUMINT;
        """
    )
    op.execute(
        """ALTER TABLE deducible 
        ADD COLUMN regimen_id MEDIUMINT;
        """
    )


def downgrade() -> None:
    op.execute(
        """ALTER TABLE conceptos 
        DROP COLUMN regimen_id;
        """
    )
    op.execute(
        """ALTER TABLE deducible 
        DROP COLUMN regimen_id;
        """
    )
