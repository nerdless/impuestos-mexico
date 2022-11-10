"""Create deducible trigger

Revision ID: 9c9558c7c025
Revises: f2e94bf57f3c
Create Date: 2022-11-10 20:36:11.458354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c9558c7c025'
down_revision = 'f2e94bf57f3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELIMITER $$
        $$
        CREATE TRIGGER get_deducible_value
        BEFORE INSERT
        ON conceptos FOR EACH ROW
            IF (SELECT 1 = 1 FROM deducible WHERE emisor_rfc=NEW.emisor_rfc and receptor_rfc=NEW.receptor_rfc and descripcion=NEW.descripcion) THEN
                SET NEW.deducible = (SELECT deducible FROM deducible WHERE emisor_rfc=NEW.emisor_rfc and receptor_rfc=NEW.receptor_rfc and descripcion=NEW.descripcion);
            ELSE
                INSERT INTO deducible (emisor_rfc, receptor_rfc, descripcion) VALUES (new.emisor_rfc, new.receptor_rfc, new.descripcion);
            END IF;$$
        DELIMITER;
        """
    )


def downgrade() -> None:
    pass
