"""Create regimen table

Revision ID: e4bd427e565d
Revises: 9c9558c7c025
Create Date: 2023-01-22 20:19:25.707319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4bd427e565d'
down_revision = '9c9558c7c025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE regimen_cat (
            id MEDIUMINT,
            description VARCHAR(250),
            PRIMARY KEY (id)
            )"""
    )


def downgrade() -> None:
    op.drop_table('regimen_cat')
