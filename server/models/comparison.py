from datetime import datetime
from . import db
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY
import uuid

class Comparison(db.Model):
    __tablename__ = 'comparisons'

    # Primary key (works with both PostgreSQL and SQLite)
    id = db.Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Upload references - supporting both single and multi-image comparisons
    main_upload_id = db.Column(String(36), db.ForeignKey('uploads.id'))
    secondary_upload_id = db.Column(String(36), db.ForeignKey('uploads.id'))

    # For multi-image comparisons (stored as JSON for SQLite compatibility)
    main_upload_ids = db.Column(JSON)  # Store as JSON array
    secondary_upload_ids = db.Column(JSON)  # Store as JSON array

    # Comparison metadata
    comparison_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comparison_type = db.Column(db.String(50), nullable=False)  # 'simple_text', 'gemini_validation', etc.

    # Validation result (stored as JSON to handle different result structures)
    validation_result = db.Column(JSON, nullable=False)

    # For text-only comparisons (when no uploads are involved)
    source_text = db.Column(db.Text)
    destination_text = db.Column(db.Text)

    # Relationships
    main_upload = db.relationship('Upload', foreign_keys=[main_upload_id], backref='main_comparisons')
    secondary_upload = db.relationship('Upload', foreign_keys=[secondary_upload_id], backref='secondary_comparisons')

    # Indexes for better query performance
    __table_args__ = (
        db.Index('idx_comparisons_comparison_date', 'comparison_date'),
        db.Index('idx_comparisons_comparison_type', 'comparison_type'),
        db.Index('idx_comparisons_main_upload_id', 'main_upload_id'),
        db.Index('idx_comparisons_secondary_upload_id', 'secondary_upload_id'),
    )

    def to_dict(self):
        """Convert comparison to dictionary for JSON response"""
        return {
            'comparison_id': str(self.id),
            'main_upload_id': str(self.main_upload_id) if self.main_upload_id else None,
            'secondary_upload_id': str(self.secondary_upload_id) if self.secondary_upload_id else None,
            'main_upload_ids': [str(uid) for uid in self.main_upload_ids] if self.main_upload_ids else None,
            'secondary_upload_ids': [str(uid) for uid in self.secondary_upload_ids] if self.secondary_upload_ids else None,
            'comparison_date': self.comparison_date.isoformat() if self.comparison_date else None,
            'comparison_type': self.comparison_type,
            'validation_result': self.validation_result,
            'source_text': self.source_text,
            'destination_text': self.destination_text
        }

    def __repr__(self):
        return f'<Comparison {self.id}: {self.comparison_type} on {self.comparison_date}>'