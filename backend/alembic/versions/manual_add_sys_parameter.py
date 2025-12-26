"""manual_add_sys_parameter

Revision ID: e3698073a33c
Revises: d9a5589fc00b
Create Date: 2025-12-24 21:12:53.818161

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'e3698073a33c'
down_revision = 'd9a5589fc00b'
branch_labels = ('custom_features',)
depends_on = None


def upgrade():
    # 手动创建 sys_parameter 表
    op.create_table('sys_parameter',
        sa.Column('pkey', sa.String(length=255), nullable=False),
        sa.Column('pval', sa.Text(), nullable=True),  # 使用 Text 类型以容纳较长的配置值
        sa.Column('group_name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('pkey')
    )
    # 创建索引
    op.create_index(op.f('ix_sys_parameter_group_name'), 'sys_parameter', ['group_name'], unique=False)


def downgrade():
    # 回滚时删除表
    op.drop_index(op.f('ix_sys_parameter_group_name'), table_name='sys_parameter')
    op.drop_table('sys_parameter')
