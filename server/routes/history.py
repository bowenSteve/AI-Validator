from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import pymongo
from bson import ObjectId
import os
import logging

history_bp = Blueprint('History', __name__)
logger = logging.getLogger(__name__)

def get_db():
    client = pymongo.MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    return client[os.getenv('MONGODB_DB_NAME', 'middesk')]

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
        db = get_db()
        uploads_collection = db.uploads
        comparisons_collection = db.comparisons
        
        # Count documents
        total_uploads = uploads_collection.count_documents({})
        total_comparisons = comparisons_collection.count_documents({})
        
        # Get a few sample records
        sample_uploads = list(uploads_collection.find({}).limit(3))
        sample_comparisons = list(comparisons_collection.find({}).limit(3))
        
        # Convert ObjectIds to strings for JSON serialization
        for upload in sample_uploads:
            upload['_id'] = str(upload['_id'])
            upload['file_id'] = str(upload['file_id'])
        
        for comparison in sample_comparisons:
            comparison['_id'] = str(comparison['_id'])
            if 'main_upload_id' in comparison:
                comparison['main_upload_id'] = str(comparison['main_upload_id'])
            if 'secondary_upload_id' in comparison:
                comparison['secondary_upload_id'] = str(comparison['secondary_upload_id'])
        
        return jsonify({
            'success': True,
            'database_status': {
                'total_uploads': total_uploads,
                'total_comparisons': total_comparisons
            },
            'sample_uploads': sample_uploads,
            'sample_comparisons': sample_comparisons,
            'collections_info': {
                'uploads_indexes': uploads_collection.index_information(),
                'comparisons_indexes': comparisons_collection.index_information()
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
        
        # Build MongoDB query
        query = {}
        
        # Date range filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    date_filter['$gte'] = start
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format. Use ISO format (YYYY-MM-DD)'}), 400
                    
            if end_date:
                try:
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    # Include the entire end day
                    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                    date_filter['$lte'] = end
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format. Use ISO format (YYYY-MM-DD)'}), 400
                    
            query['upload_date'] = date_filter
        
        # Image type filter
        if image_type and image_type != 'all':
            if image_type not in ['main', 'secondary']:
                return jsonify({'error': 'Invalid image_type. Must be "main", "secondary", or "all"'}), 400
            query['image_type'] = image_type
        
        db = get_db()
        uploads_collection = db.uploads
        
        # Get total count for pagination
        total = uploads_collection.count_documents(query)
        
        # Set sort order
        sort_direction = -1 if sort_order == 'newest' else 1
        
        # Get paginated results
        uploads = uploads_collection.find(query).sort('upload_date', sort_direction).skip((page - 1) * limit).limit(limit)
        
        upload_list = []
        for upload in uploads:
            gemini_data = upload.get('gemini_processing', {})
            
            # Handle both old and new upload formats
            has_gemini_processing = 'gemini_processing' in upload
            
            upload_data = {
                'upload_id': str(upload['_id']),
                'file_id': str(upload['file_id']),
                'filename': upload.get('filename', upload.get('original_filename', 'unknown')),
                'original_filename': upload.get('original_filename', ''),
                'image_type': upload['image_type'],
                'content_type': upload.get('content_type', ''),
                'file_size': upload['file_size'],
                'original_size': upload.get('original_size', upload['file_size']),
                'upload_date': upload['upload_date'].isoformat(),
                'status': upload['status'],
                'has_text_extraction': has_gemini_processing,
                'extracted_text': gemini_data.get('extracted_text', '') if has_gemini_processing else '',
                'text_extraction_success': gemini_data.get('processed', False) if has_gemini_processing else None,
                'text_extraction_error': gemini_data.get('error', None) if has_gemini_processing else None,
                'processed_at': gemini_data.get('processed_at').isoformat() if gemini_data.get('processed_at') else None,
                'gemini_result': gemini_data.get('result', {}) if has_gemini_processing else {}
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
        
        db = get_db()
        uploads_collection = db.uploads
        
        # Base query with date filter
        base_query = {'upload_date': date_filter} if date_filter else {}
        
        # Get statistics
        total_uploads = uploads_collection.count_documents(base_query)
        
        main_uploads = uploads_collection.count_documents({**base_query, 'image_type': 'main'})
        secondary_uploads = uploads_collection.count_documents({**base_query, 'image_type': 'secondary'})
        
        # Text extraction stats
        successful_extractions = uploads_collection.count_documents({
            **base_query, 
            'gemini_processing.processed': True
        })
        failed_extractions = uploads_collection.count_documents({
            **base_query, 
            'gemini_processing.processed': False
        })
        # Count records where gemini_processing doesn't exist or processed field is missing
        pending_extractions = uploads_collection.count_documents({
            **base_query,
            '$or': [
                {'gemini_processing': {'$exists': False}},
                {'gemini_processing.processed': {'$exists': False}}
            ]
        })
        
        # Calculate total file size
        pipeline = [
            {'$match': base_query},
            {'$group': {'_id': None, 'total_size': {'$sum': '$file_size'}}}
        ]
        size_result = list(uploads_collection.aggregate(pipeline))
        total_file_size = size_result[0]['total_size'] if size_result else 0
        
        # Get uploads by date (last 30 days or within date range)
        if not date_filter:
            # Default to last 30 days if no date filter
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            date_filter = {'$gte': thirty_days_ago}
        
        daily_pipeline = [
            {'$match': {**base_query, 'upload_date': date_filter}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$upload_date'},
                    'month': {'$month': '$upload_date'},
                    'day': {'$dayOfMonth': '$upload_date'}
                },
                'count': {'$sum': 1},
                'main_count': {'$sum': {'$cond': [{'$eq': ['$image_type', 'main']}, 1, 0]}},
                'secondary_count': {'$sum': {'$cond': [{'$eq': ['$image_type', 'secondary']}, 1, 0]}}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]
        
        daily_stats = []
        for day in uploads_collection.aggregate(daily_pipeline):
            date_str = f"{day['_id']['year']}-{day['_id']['month']:02d}-{day['_id']['day']:02d}"
            daily_stats.append({
                'date': date_str,
                'total': day['count'],
                'main': day['main_count'],
                'secondary': day['secondary_count']
            })
        
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
        db = get_db()
        uploads_collection = db.uploads
        
        upload = uploads_collection.find_one({'_id': ObjectId(upload_id)})
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        upload_detail = {
            'upload_id': str(upload['_id']),
            'file_id': str(upload['file_id']),
            'filename': upload['filename'],
            'original_filename': upload['original_filename'],
            'image_type': upload['image_type'],
            'content_type': upload['content_type'],
            'file_size': upload['file_size'],
            'original_size': upload.get('original_size', upload['file_size']),
            'upload_date': upload['upload_date'].isoformat(),
            'status': upload['status'],
            'gemini_processing': {
                'processed': upload.get('gemini_processing', {}).get('processed', False),
                'processed_at': upload.get('gemini_processing', {}).get('processed_at').isoformat() if upload.get('gemini_processing', {}).get('processed_at') else None,
                'extracted_text': upload.get('gemini_processing', {}).get('extracted_text', ''),
                'error': upload.get('gemini_processing', {}).get('error'),
                'result': upload.get('gemini_processing', {}).get('result', {})
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
        db = get_db()
        uploads_collection = db.uploads
        
        # Find the upload
        upload = uploads_collection.find_one({'_id': ObjectId(upload_id)})
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Delete from GridFS
        import gridfs
        fs = gridfs.GridFS(db)
        try:
            fs.delete(upload['file_id'])
        except gridfs.NoFile:
            pass  # File already deleted
        
        # Delete upload record
        uploads_collection.delete_one({'_id': ObjectId(upload_id)})
        
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
        
        # Build MongoDB query
        query = {}
        
        # Date range filter
        if start_date or end_date:
            date_filter = {}
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
                    
            query['comparison_date'] = date_filter
        
        # Comparison type filter
        if comparison_type and comparison_type != 'all':
            if comparison_type not in ['simple_text', 'gemini_validation', 'simple_text_only']:
                return jsonify({'error': 'Invalid comparison_type'}), 400
            query['comparison_type'] = comparison_type
        
        db = get_db()
        comparisons_collection = db.comparisons
        
        # Get total count
        total = comparisons_collection.count_documents(query)
        
        # Set sort order
        sort_direction = -1 if sort_order == 'newest' else 1
        
        # Get paginated results
        comparisons = comparisons_collection.find(query).sort('comparison_date', sort_direction).skip((page - 1) * limit).limit(limit)
        
        comparison_list = []
        for comp in comparisons:
            validation_result = comp.get('validation_result', {})
            
            comparison_data = {
                'comparison_id': str(comp['_id']),
                'main_upload_id': str(comp['main_upload_id']) if 'main_upload_id' in comp else None,
                'secondary_upload_id': str(comp['secondary_upload_id']) if 'secondary_upload_id' in comp else None,
                'comparison_date': comp['comparison_date'].isoformat(),
                'comparison_type': comp.get('comparison_type', 'simple_text'),
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