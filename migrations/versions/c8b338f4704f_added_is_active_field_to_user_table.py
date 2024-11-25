"""Added is_active field to User table

Revision ID: c8b338f4704f
Revises: 42b2faa1502d
Create Date: 2024-11-24 16:34:39.505338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8b338f4704f'
down_revision = '42b2faa1502d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('component', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('component', schema=None) as batch_op:
        batch_op.drop_column('is_active')

    # ### end Alembic commands ###