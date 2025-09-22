from datetime import datetime
from . import db
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

class Upload(db.Model):
    __tablename__ = 'uploads'

    # Primary key (works with both PostgreSQL and SQLite)
    id = db.Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    image_type = db.Column(db.String(20), nullable=False)  # 'main' or 'secondary'
    content_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    original_size = db.Column(db.BigInteger, nullable=False)

    # Store binary data directly in PostgreSQL (replacing GridFS)
    file_data = db.Column(db.LargeBinary, nullable=False)

    # Upload metadata
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='uploaded')

    # Gemini processing results (stored as JSON)
    gemini_processed = db.Column(db.Boolean, default=False)
    gemini_processed_at = db.Column(db.DateTime)
    gemini_extracted_text = db.Column(db.Text)
    gemini_confidence_score = db.Column(db.Float, default=0.0)
    gemini_has_uncertainties = db.Column(db.Boolean, default=False)
    gemini_validation = db.Column(JSON)
    gemini_result = db.Column(JSON)
    gemini_error = db.Column(db.Text)
    gemini_reprocessed_at = db.Column(db.DateTime)

    # Indexes for better query performance
    __table_args__ = (
        db.Index('idx_uploads_image_type', 'image_type'),
        db.Index('idx_uploads_upload_date', 'upload_date'),
        db.Index('idx_uploads_status', 'status'),
        db.Index('idx_uploads_gemini_processed', 'gemini_processed'),
    )

    def to_dict(self, include_file_data=False):
        """Convert upload to dictionary for JSON response"""
        result = {
            'upload_id': str(self.id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'image_type': self.image_type,
            'content_type': self.content_type,
            'file_size': self.file_size,
            'original_size': self.original_size,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'status': self.status,
            'gemini_processing': {
                'processed': self.gemini_processed,
                'processed_at': self.gemini_processed_at.isoformat() if self.gemini_processed_at else None,
                'extracted_text': self.gemini_extracted_text or '',
                'confidence_score': self.gemini_confidence_score or 0.0,
                'has_uncertainties': self.gemini_has_uncertainties or False,
                'validation': self.gemini_validation or {},
                'result': self.gemini_result or {},
                'error': self.gemini_error,
                'reprocessed_at': self.gemini_reprocessed_at.isoformat() if self.gemini_reprocessed_at else None
            }
        }

        if include_file_data:
            result['file_data'] = self.file_data

        return result

    def __repr__(self):
        return f'<Upload {self.id}: {self.original_filename} ({self.image_type})>'