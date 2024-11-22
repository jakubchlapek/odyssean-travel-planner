"""Added the database, needed to recreate

Revision ID: 2c7e14750789
Revises: 
Create Date: 2024-11-20 14:36:15.565304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c7e14750789'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('component_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category_name', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('component_category', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_component_category_category_name'), ['category_name'], unique=True)

    op.create_table('exchange_rates',
    sa.Column('currency_to', sa.String(length=3), nullable=False),
    sa.Column('rate', sa.DECIMAL(precision=18, scale=9), nullable=False),
    sa.Column('last_updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('currency_to')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=12), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.Column('preferred_currency', sa.String(length=3), nullable=True),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('component_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('type_name', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['component_category.id'], name='fk_component_type_category_id'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('component_type', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_component_type_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_component_type_type_name'), ['type_name'], unique=False)

    op.create_table('trip',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('trip_name', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_trip_user_id'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_trip_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_trip_user_id'), ['user_id'], unique=False)

    op.create_table('component',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('component_name', sa.String(length=64), nullable=False),
    sa.Column('base_cost', sa.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('link', sa.String(length=2083), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['component_category.id'], name='fk_component_category_id'),
    sa.ForeignKeyConstraint(['trip_id'], ['trip.id'], name='fk_component_trip_id', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['type_id'], ['component_type.id'], name='fk_component_type_id'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('component', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_component_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_component_trip_id'), ['trip_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_component_type_id'), ['type_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('component', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_component_type_id'))
        batch_op.drop_index(batch_op.f('ix_component_trip_id'))
        batch_op.drop_index(batch_op.f('ix_component_category_id'))

    op.drop_table('component')
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_trip_user_id'))
        batch_op.drop_index(batch_op.f('ix_trip_created_at'))

    op.drop_table('trip')
    with op.batch_alter_table('component_type', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_component_type_type_name'))
        batch_op.drop_index(batch_op.f('ix_component_type_category_id'))

    op.drop_table('component_type')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))
        batch_op.drop_index(batch_op.f('ix_user_created_at'))

    op.drop_table('user')
    op.drop_table('exchange_rates')
    with op.batch_alter_table('component_category', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_component_category_category_name'))

    op.drop_table('component_category')
    # ### end Alembic commands ###