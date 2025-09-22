from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import os
import logging
from sqlalchemy import func, and_, or_

# Import SQLAlchemy models
from .models import db, Upload, Comparison

history_bp = Blueprint('History', __name__)
logger = logging.getLogger(__name__)

@history_bp.route('/', methods=['GET'])
def history_index():
    """
    History API index - lists available endpoints
    """
    return jsonify({
        'message': 'History API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/history/uploads': 'Get upload history with optional filtering',
            'GET /api/history/uploads/stats': 'Get upload statistics',
            'GET /api/history/uploads/{upload_id}': 'Get specific upload details',
            'GET /api/history/debug': 'Debug database content',
            'DELETE /api/history/uploads/{upload_id}': 'Delete upload from history'
        }
    }), 200

@history_bp.route('/debug', methods=['GET'])
def debug_database():
    """
    Debug endpoint to check what's actually in the database
    """
    try:
        # Count documents
        total_uploads = Upload.query.count()
        total_comparisons = Comparison.query.count()

        # Get a few sample records
        sample_uploads = Upload.query.limit(3).all()
        sample_comparisons = Comparison.query.limit(3).all()

        # Convert to dictionaries for JSON serialization
        sample_uploads_dict = []
        for upload in sample_uploads:
            upload_dict = upload.to_dict()
            # Don't include file_data in debug output
            upload_dict.pop('file_data', None)
            sample_uploads_dict.append(upload_dict)

        sample_comparisons_dict = [comp.to_dict() for comp in sample_comparisons]

        return jsonify({
            'success': True,
            'database_status': {
                'total_uploads': total_uploads,
                'total_comparisons': total_comparisons
            },
            'sample_uploads': sample_uploads_dict,
            'sample_comparisons': sample_comparisons_dict,
            'database_info': {
                'upload_table': 'uploads',
                'comparison_table': 'comparisons'
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Debug database error: {str(e)}")
        return jsonify({'error': 'Debug failed', 'details': str(e)}), 500

@history_bp.route('/uploads', methods=['GET'])
def get_upload_history():
    """
    Get upload history with optional date filtering
    Query params:
    - start_date: ISO date string (e.g., '2024-01-01')
    - end_date: ISO date string (e.g., '2024-01-31')
    - image_type: 'main', 'secondary', or 'all' (default)
    - page: page number (default 1)
    - limit: items per page (default 20, max 100)
    - sort: 'newest' or 'oldest' (default 'newest')
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        image_type = request.args.get('image_type', 'all')
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)  # Cap at 100
        sort_order = request.args.get('sort', 'newest')
        
        # Build SQLAlchemy query
        query = Upload.query

        # Date range filter
        if start_date or end_date:
            if start_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Upload.upload_date >= start)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format. Use ISO format (YYYY-MM-DD)'}), 400

            if end_date:
                try:
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    # Include the entire end day
                    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                    query = query.filter(Upload.upload_date <= end)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format. Use ISO format (YYYY-MM-DD)'}), 400

        # Image type filter
        if image_type and image_type != 'all':
            if image_type not in ['main', 'secondary']:
                return jsonify({'error': 'Invalid image_type. Must be "main", "secondary", or "all"'}), 400
            query = query.filter(Upload.image_type == image_type)

        # Get total count for pagination
        total = query.count()

        # Set sort order
        if sort_order == 'newest':
            query = query.order_by(Upload.upload_date.desc())
        else:
            query = query.order_by(Upload.upload_date.asc())

        # Get paginated results
        uploads = query.offset((page - 1) * limit).limit(limit).all()
        
        upload_list = []
        for upload in uploads:
            upload_data = {
                'upload_id': str(upload.id),
                'filename': upload.filename,
                'original_filename': upload.original_filename,
                'image_type': upload.image_type,
                'content_type': upload.content_type,
                'file_size': upload.file_size,
                'original_size': upload.original_size,
                'upload_date': upload.upload_date.isoformat(),
                'status': upload.status,
                'has_text_extraction': upload.gemini_processed,
                'extracted_text': upload.gemini_extracted_text or '',
                'text_extraction_success': upload.gemini_processed,
                'text_extraction_error': upload.gemini_error,
                'processed_at': upload.gemini_processed_at.isoformat() if upload.gemini_processed_at else None,
                'gemini_result': upload.gemini_result or {}
            }
            upload_list.append(upload_data)
        
        return jsonify({
            'success': True,
            'uploads': upload_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
                'has_next': page * limit < total,
                'has_prev': page > 1
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'image_type': image_type,
                'sort': sort_order
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get upload history error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve upload history'}), 500

@history_bp.route('/uploads/stats', methods=['GET'])
def get_upload_stats():
    """
    Get upload statistics
    Query params:
    - start_date: ISO date string (optional)
    - end_date: ISO date string (optional)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build date filter
        date_filter = {}
        if start_date or end_date:
            if start_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    date_filter['$gte'] = start
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format'}), 400
                    
            if end_date:
                try:
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                    date_filter['$lte'] = end
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Base query with date filter
        base_query = Upload.query
        if date_filter:
            if '$gte' in date_filter:
                base_query = base_query.filter(Upload.upload_date >= date_filter['$gte'])
            if '$lte' in date_filter:
                base_query = base_query.filter(Upload.upload_date <= date_filter['$lte'])

        # Get statistics
        total_uploads = base_query.count()

        main_uploads = base_query.filter(Upload.image_type == 'main').count()
        secondary_uploads = base_query.filter(Upload.image_type == 'secondary').count()

        # Text extraction stats
        successful_extractions = base_query.filter(Upload.gemini_processed == True).count()
        failed_extractions = base_query.filter(Upload.gemini_processed == False).count()
        pending_extractions = base_query.filter(Upload.gemini_processed == None).count()

        # Calculate total file size
        total_file_size = db.session.query(func.sum(Upload.file_size)).filter(
            Upload.id.in_([u.id for u in base_query.all()])
        ).scalar() or 0
        
        # Get daily stats (simplified for now - could be enhanced with proper SQL aggregation)
        daily_stats = []

        # For now, just return empty daily stats (this would need proper SQL aggregation for production)
        # TODO: Implement proper daily statistics aggregation using SQL
        
        return jsonify({
            'success': True,
            'stats': {
                'total_uploads': total_uploads,
                'main_uploads': main_uploads,
                'secondary_uploads': secondary_uploads,
                'successful_text_extractions': successful_extractions,
                'failed_text_extractions': failed_extractions,
                'pending_text_extractions': pending_extractions,
                'text_extraction_rate': round((successful_extractions / total_uploads * 100), 2) if total_uploads > 0 else 0,
                'total_file_size_bytes': total_file_size,
                'total_file_size_mb': round(total_file_size / (1024 * 1024), 2)
            },
            'daily_stats': daily_stats,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get upload stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve upload statistics'}), 500

@history_bp.route('/uploads/<upload_id>', methods=['GET'])
def get_upload_detail(upload_id):
    """
    Get detailed information for a specific upload
    """
    try:
        upload = Upload.query.filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        upload_detail = {
            'upload_id': str(upload.id),
            'filename': upload.filename,
            'original_filename': upload.original_filename,
            'image_type': upload.image_type,
            'content_type': upload.content_type,
            'file_size': upload.file_size,
            'original_size': upload.original_size,
            'upload_date': upload.upload_date.isoformat(),
            'status': upload.status,
            'gemini_processing': {
                'processed': upload.gemini_processed or False,
                'processed_at': upload.gemini_processed_at.isoformat() if upload.gemini_processed_at else None,
                'extracted_text': upload.gemini_extracted_text or '',
                'error': upload.gemini_error,
                'result': upload.gemini_result or {}
            }
        }
        
        return jsonify({
            'success': True,
            'upload': upload_detail
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get upload detail error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve upload details'}), 500

@history_bp.route('/uploads/<upload_id>', methods=['DELETE'])
def delete_upload_from_history(upload_id):
    """
    Delete an upload from history
    """
    try:
        # Find the upload
        upload = Upload.query.filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        # Delete upload record (file data is stored in the record itself)
        db.session.delete(upload)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Upload deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete upload error: {str(e)}")
        return jsonify({'error': 'Failed to delete upload'}), 500

@history_bp.route('/validations', methods=['GET'])
def get_validation_history():
    """
    Get validation/comparison history with optional filtering
    Query params:
    - start_date: ISO date string (e.g., '2024-01-01')
    - end_date: ISO date string (e.g., '2024-01-31')
    - comparison_type: 'simple_text', 'gemini_validation', or 'all' (default)
    - page: page number (default 1)
    - limit: items per page (default 20, max 100)
    - sort: 'newest' or 'oldest' (default 'newest')
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        comparison_type = request.args.get('comparison_type', 'all')
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        sort_order = request.args.get('sort', 'newest')
        
        # Build SQLAlchemy query
        query = Comparison.query

        # Date range filter
        if start_date or end_date:
            if start_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Comparison.comparison_date >= start)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format'}), 400

            if end_date:
                try:
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                    query = query.filter(Comparison.comparison_date <= end)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format'}), 400

        # Comparison type filter
        if comparison_type and comparison_type != 'all':
            if comparison_type not in ['simple_text', 'gemini_validation', 'simple_text_only']:
                return jsonify({'error': 'Invalid comparison_type'}), 400
            query = query.filter(Comparison.comparison_type == comparison_type)

        # Get total count
        total = query.count()

        # Set sort order
        if sort_order == 'newest':
            query = query.order_by(Comparison.comparison_date.desc())
        else:
            query = query.order_by(Comparison.comparison_date.asc())

        # Get paginated results
        comparisons = query.offset((page - 1) * limit).limit(limit).all()
        
        comparison_list = []
        for comp in comparisons:
            validation_result = comp.validation_result or {}

            comparison_data = {
                'comparison_id': str(comp.id),
                'main_upload_id': str(comp.main_upload_id) if comp.main_upload_id else None,
                'secondary_upload_id': str(comp.secondary_upload_id) if comp.secondary_upload_id else None,
                'comparison_date': comp.comparison_date.isoformat(),
                'comparison_type': comp.comparison_type,
                'validation_result': validation_result,
                # Summary fields for easy access
                'accuracy_score': validation_result.get('accuracy_score', validation_result.get('overall_similarity', 0)),
                'is_successful': validation_result.get('is_successful_transfer', None),
                'total_fields': validation_result.get('total_fields_identified', validation_result.get('total_lines', 0)),
                'matched_fields': validation_result.get('fields_transferred_correctly', validation_result.get('matched_lines', 0))
            }
            comparison_list.append(comparison_data)
        
        return jsonify({
            'success': True,
            'validations': comparison_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
                'has_next': page * limit < total,
                'has_prev': page > 1
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'comparison_type': comparison_type,
                'sort': sort_order
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get validation history error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve validation history'}), 500