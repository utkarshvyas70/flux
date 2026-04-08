"""initial schema

Revision ID: 0df9f064d624
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0df9f064d624'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users first (no dependencies)
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. workspaces (depends on users)
    op.create_table('workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. workspace_members (depends on users, workspaces)
    op.create_table('workspace_members',
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('owner', 'member', name='memberrole'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('workspace_id', 'user_id')
    )

    # 4. repositories (depends on workspaces)
    op.create_table('repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. prompt_versions WITHOUT the branch_id FK first (we add it after branches)
    op.create_table('prompt_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('model_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('commit_message', sa.String(), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('eval_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. branches (depends on repositories and prompt_versions)
    op.create_table('branches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_from_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_from_version_id'], ['prompt_versions.id']),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Now add the branch_id FK to prompt_versions
    op.create_foreign_key(
        'fk_prompt_versions_branch_id',
        'prompt_versions', 'branches',
        ['branch_id'], ['id']
    )

    # 8. eval_suites (depends on repositories)
    op.create_table('eval_suites',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. eval_cases (depends on eval_suites)
    op.create_table('eval_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('suite_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('eval_type', sa.Enum('exact', 'similarity', 'llm_judge', name='evaltype'), nullable=False),
        sa.ForeignKeyConstraint(['suite_id'], ['eval_suites.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. eval_runs (depends on prompt_versions and eval_suites)
    op.create_table('eval_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('suite_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='evalrunstatus'), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['suite_id'], ['eval_suites.id']),
        sa.ForeignKeyConstraint(['version_id'], ['prompt_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('eval_runs')
    op.drop_table('eval_cases')
    op.drop_table('eval_suites')
    op.drop_constraint('fk_prompt_versions_branch_id', 'prompt_versions', type_='foreignkey')
    op.drop_table('branches')
    op.drop_table('prompt_versions')
    op.drop_table('repositories')
    op.drop_table('workspace_members')
    op.drop_table('workspaces')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS memberrole')
    op.execute('DROP TYPE IF EXISTS evaltype')
    op.execute('DROP TYPE IF EXISTS evalrunstatus')