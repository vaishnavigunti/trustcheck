"""Initial migration with all tables

Revision ID: 2171d4e40e95
Revises: 
Create Date: 2026-06-18 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2171d4e40e95'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by_ip', sa.String(length=45), nullable=True),
        sa.Column('device_info', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    # Create verifications table
    op.create_table(
        'verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_type', sa.Enum('COMPANY', 'RECRUITER', 'OFFER_LETTER', 'WEBSITE', name='verificationtype'), nullable=False),
        sa.Column('target_url', sa.String(length=2048), nullable=True),
        sa.Column('recruiter_email', sa.String(length=255), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='verificationstatus'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('verification_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verifications_recruiter_email'), 'verifications', ['recruiter_email'], unique=False)
    op.create_index(op.f('ix_verifications_status'), 'verifications', ['status'], unique=False)
    op.create_index(op.f('ix_verifications_user_id'), 'verifications', ['user_id'], unique=False)

    # Create verification_findings table
    op.create_table(
        'verification_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.Enum('DOMAIN', 'SSL', 'DNS', 'EMAIL', 'WEBSITE', 'PDF', 'SYSTEM', name='findingcategory'), nullable=False),
        sa.Column('check_name', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.Enum('PASSED', 'INFO', 'WARNING', 'CRITICAL', name='findingseverity'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['verification_id'], ['verifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_findings_category'), 'verification_findings', ['category'], unique=False)
    op.create_index(op.f('ix_verification_findings_severity'), 'verification_findings', ['severity'], unique=False)
    op.create_index(op.f('ix_verification_findings_verification_id'), 'verification_findings', ['verification_id'], unique=False)

    # Create evidence_timeline table
    op.create_table(
        'evidence_timeline',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.Enum('VERIFICATION_STARTED', 'DOMAIN_CHECK', 'SSL_CHECK', 'DNS_CHECK', 'WEBSITE_ANALYSIS', 'EMAIL_VERIFICATION', 'PDF_EXTRACTION', 'CROSS_VALIDATION', 'VERIFICATION_COMPLETED', 'VERIFICATION_FAILED', name='timelineeventtype'), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['verification_id'], ['verifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_timeline_verification_id'), 'evidence_timeline', ['verification_id'], unique=False)

    # Create uploaded_files table
    op.create_table(
        'uploaded_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['verification_id'], ['verifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stored_filename')
    )
    op.create_index(op.f('ix_uploaded_files_file_hash'), 'uploaded_files', ['file_hash'], unique=False)
    op.create_index(op.f('ix_uploaded_files_verification_id'), 'uploaded_files', ['verification_id'], unique=False)

    # Create pdf_extracted_data table
    op.create_table(
        'pdf_extracted_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extracted_company_name', sa.String(length=255), nullable=True),
        sa.Column('extracted_email', sa.String(length=255), nullable=True),
        sa.Column('extracted_website', sa.String(length=2048), nullable=True),
        sa.Column('extracted_address', sa.Text(), nullable=True),
        sa.Column('extracted_phone', sa.String(length=50), nullable=True),
        sa.Column('extracted_position', sa.String(length=255), nullable=True),
        sa.Column('extracted_salary', sa.String(length=100), nullable=True),
        sa.Column('extracted_start_date', sa.String(length=100), nullable=True),
        sa.Column('other_entities', sa.JSON(), nullable=False),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('extraction_errors', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['verification_id'], ['verifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('verification_id')
    )
    op.create_index(op.f('ix_pdf_extracted_data_verification_id'), 'pdf_extracted_data', ['verification_id'], unique=True)

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('GENERATING', 'COMPLETED', 'FAILED', name='reportstatus'), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verification_id'], ['verifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_user_id'), 'reports', ['user_id'], unique=False)
    op.create_index(op.f('ix_reports_verification_id'), 'reports', ['verification_id'], unique=False)

    # Create shared_reports table
    op.create_table(
        'shared_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accessed_count', sa.Integer(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_ip', sa.String(length=45), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_shared_reports_report_id'), 'shared_reports', ['report_id'], unique=False)
    op.create_index(op.f('ix_shared_reports_token'), 'shared_reports', ['token'], unique=True)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.Enum('LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'PASSWORD_CHANGED', 'TOKEN_REFRESHED', 'TOKEN_REVOKED', 'USER_REGISTERED', 'USER_UPDATED', 'USER_DELETED', 'VERIFICATION_CREATED', 'VERIFICATION_VIEWED', 'VERIFICATION_DELETED', 'REPORT_GENERATED', 'REPORT_DOWNLOADED', 'REPORT_SHARED', 'SHARED_REPORT_ACCESSED', 'FILE_UPLOADED', 'FILE_DELETED', 'ADMIN_ACTION', name='auditaction'), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_shared_reports_token'), table_name='shared_reports')
    op.drop_index(op.f('ix_shared_reports_report_id'), table_name='shared_reports')
    op.drop_table('shared_reports')

    op.drop_index(op.f('ix_reports_verification_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_user_id'), table_name='reports')
    op.drop_table('reports')

    op.drop_index(op.f('ix_pdf_extracted_data_verification_id'), table_name='pdf_extracted_data')
    op.drop_table('pdf_extracted_data')

    op.drop_index(op.f('ix_uploaded_files_verification_id'), table_name='uploaded_files')
    op.drop_index(op.f('ix_uploaded_files_file_hash'), table_name='uploaded_files')
    op.drop_table('uploaded_files')

    op.drop_index(op.f('ix_evidence_timeline_verification_id'), table_name='evidence_timeline')
    op.drop_table('evidence_timeline')

    op.drop_index(op.f('ix_verification_findings_verification_id'), table_name='verification_findings')
    op.drop_index(op.f('ix_verification_findings_severity'), table_name='verification_findings')
    op.drop_index(op.f('ix_verification_findings_category'), table_name='verification_findings')
    op.drop_table('verification_findings')

    op.drop_index(op.f('ix_verifications_user_id'), table_name='verifications')
    op.drop_index(op.f('ix_verifications_status'), table_name='verifications')
    op.drop_index(op.f('ix_verifications_recruiter_email'), table_name='verifications')
    op.drop_table('verifications')

    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.execute("DROP TYPE IF EXISTS reportstatus")
    op.execute("DROP TYPE IF EXISTS timelineeventtype")
    op.execute("DROP TYPE IF EXISTS findingseverity")
    op.execute("DROP TYPE IF EXISTS findingcategory")
    op.execute("DROP TYPE IF EXISTS verificationstatus")
    op.execute("DROP TYPE IF EXISTS verificationtype")
