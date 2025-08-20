from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import pymongo
from bson import ObjectId
import logging
import os

# Import our simple text comparison service
from services.simple_text_comparison import simple_text_comparison
from services.gemini_validator import gemini_validator

simple_validation_bp = Blueprint('SimpleValidation', __name__, url_prefix='/api/validation')
logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    client = pymongo.MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    return client[os.getenv('MONGODB_DB_NAME', 'middesk')]


@simple_validation_bp.route('/compare/gemini', methods=['POST'])
def compare_uploads_with_gemini():
    """
    Compare two uploaded images using Gemini AI for intelligent validation
    Expects: JSON with 'main_upload_id' and 'secondary_upload_id'
    """
    try:
        data = request.get_json()
        
        if not data or 'main_upload_id' not in data or 'secondary_upload_id' not in data:
            return jsonify({
                'error': 'Both main_upload_id and secondary_upload_id are required'
            }), 400
        
        main_upload_id = data['main_upload_id']
        secondary_upload_id = data['secondary_upload_id']
        
        # Get the upload records from database
        db = get_db()
        uploads_collection = db.uploads
        
        main_upload = uploads_collection.find_one({
            '_id': ObjectId(main_upload_id),
            'image_type': 'main'
        })
        
        secondary_upload = uploads_collection.find_one({
            '_id': ObjectId(secondary_upload_id),
            'image_type': 'secondary'
        })
        
        if not main_upload:
            return jsonify({'error': 'Main upload not found'}), 404
        
        if not secondary_upload:
            return jsonify({'error': 'Secondary upload not found'}), 404
        
        # Extract the text from both uploads
        main_text = main_upload.get('gemini_processing', {}).get('extracted_text', '')
        secondary_text = secondary_upload.get('gemini_processing', {}).get('extracted_text', '')
        
        if not main_text:
            return jsonify({
                'error': 'No text extracted from main image. Please ensure the image was processed successfully.'
            }), 400
        
        if not secondary_text:
            return jsonify({
                'error': 'No text extracted from secondary image. Please ensure the image was processed successfully.'
            }), 400
        
        logger.info(f"Starting Gemini validation between main upload {main_upload_id} and secondary upload {secondary_upload_id}")
        
        # Perform the Gemini validation
        success, validation_result = gemini_validator.validate_data_transfer(main_text, secondary_text)
        
        if not success:
            return jsonify({
                'error': 'Gemini validation failed',
                'details': validation_result.get('error', 'Unknown error')
            }), 500
        
        # Store the comparison result in database
        comparison_record = {
            'main_upload_id': ObjectId(main_upload_id),
            'secondary_upload_id': ObjectId(secondary_upload_id),
            'comparison_date': datetime.utcnow(),
            'comparison_type': 'gemini_validation',
            'validation_result': validation_result
        }
        
        # Store in comparisons collection
        comparisons_collection = db.comparisons
        result = comparisons_collection.insert_one(comparison_record)
        
        logger.info(f"Gemini validation completed with accuracy: {validation_result.get('accuracy_score', 0)}%")
        
        return jsonify({
            'success': True,
            'comparison_id': str(result.inserted_id),
            'validation_result': validation_result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Gemini validation error: {str(e)}")
        return jsonify({
            'error': 'Validation failed',
            'details': str(e)
        }), 500

@simple_validation_bp.route('/compare', methods=['POST'])
def compare_uploads():
    """
    Compare two uploaded images using simple text comparison
    Expects: JSON with 'main_upload_id' and 'secondary_upload_id'
    """
    try:
        data = request.get_json()
        
        if not data or 'main_upload_id' not in data or 'secondary_upload_id' not in data:
            return jsonify({
                'error': 'Both main_upload_id and secondary_upload_id are required'
            }), 400
        
        main_upload_id = data['main_upload_id']
        secondary_upload_id = data['secondary_upload_id']
        
        # Get the upload records from database
        db = get_db()
        uploads_collection = db.uploads
        
        main_upload = uploads_collection.find_one({
            '_id': ObjectId(main_upload_id),
            'image_type': 'main'
        })
        
        secondary_upload = uploads_collection.find_one({
            '_id': ObjectId(secondary_upload_id),
            'image_type': 'secondary'
        })
        
        if not main_upload:
            return jsonify({'error': 'Main upload not found'}), 404
        
        if not secondary_upload:
            return jsonify({'error': 'Secondary upload not found'}), 404
        
        # Extract the text from both uploads
        main_text = main_upload.get('gemini_processing', {}).get('extracted_text', '')
        secondary_text = secondary_upload.get('gemini_processing', {}).get('extracted_text', '')
        
        if not main_text:
            return jsonify({
                'error': 'No text extracted from main image. Please ensure the image was processed successfully.'
            }), 400
        
        if not secondary_text:
            return jsonify({
                'error': 'No text extracted from secondary image. Please ensure the image was processed successfully.'
            }), 400
        
        logger.info(f"Starting text comparison between main upload {main_upload_id} and secondary upload {secondary_upload_id}")
        
        # Perform the comparison
        validation_result = simple_text_comparison.compare_texts(main_text, secondary_text)
        
        # Store the comparison result in database
        comparison_record = {
            'main_upload_id': ObjectId(main_upload_id),
            'secondary_upload_id': ObjectId(secondary_upload_id),
            'comparison_date': datetime.utcnow(),
            'comparison_type': 'simple_text',
            'validation_result': {
                'overall_similarity': validation_result.overall_similarity,
                'total_lines': validation_result.total_lines,
                'matched_lines': validation_result.matched_lines,
                'missing_lines': validation_result.missing_lines,
                'extra_lines': validation_result.extra_lines,
                'character_accuracy': validation_result.character_accuracy,
                'word_accuracy': validation_result.word_accuracy,
                'text_matches': [
                    {
                        'source_text': tm.source_text,
                        'dest_text': tm.dest_text,
                        'match_score': tm.match_score,
                        'match_type': tm.match_type,
                        'line_number': tm.line_number,
                        'issues': tm.issues
                    } for tm in validation_result.text_matches
                ],
                'recommendations': validation_result.recommendations
            }
        }
        
        # Store in comparisons collection
        comparisons_collection = db.comparisons
        result = comparisons_collection.insert_one(comparison_record)
        
        logger.info(f"Text comparison completed with overall similarity: {validation_result.overall_similarity:.1f}%")
        
        return jsonify({
            'success': True,
            'comparison_id': str(result.inserted_id),
            'validation_result': {
                'overall_similarity': round(validation_result.overall_similarity, 1),
                'total_lines': validation_result.total_lines,
                'matched_lines': validation_result.matched_lines,
                'missing_lines': validation_result.missing_lines,
                'extra_lines': validation_result.extra_lines,
                'character_accuracy': round(validation_result.character_accuracy, 1),
                'word_accuracy': round(validation_result.word_accuracy, 1),
                'text_matches': [
                    {
                        'source_text': tm.source_text,
                        'dest_text': tm.dest_text,
                        'match_score': round(tm.match_score, 1),
                        'match_type': tm.match_type,
                        'line_number': tm.line_number,
                        'issues': tm.issues
                    } for tm in validation_result.text_matches
                ],
                'recommendations': validation_result.recommendations
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Text comparison error: {str(e)}")
        return jsonify({
            'error': 'Comparison failed',
            'details': str(e)
        }), 500

@simple_validation_bp.route('/compare/text', methods=['POST'])
def compare_raw_text():
    """
    Compare raw text directly without uploading images
    Expects: JSON with 'source_text' and 'destination_text'
    """
    try:
        data = request.get_json()
        
        if not data or 'source_text' not in data or 'destination_text' not in data:
            return jsonify({
                'error': 'Both source_text and destination_text are required'
            }), 400
        
        source_text = data['source_text']
        destination_text = data['destination_text']
        
        if not source_text.strip() or not destination_text.strip():
            return jsonify({
                'error': 'Both source and destination text must be non-empty'
            }), 400
        
        logger.info("Starting direct text comparison")
        
        # Perform the comparison
        validation_result = simple_text_comparison.compare_texts(source_text, destination_text)
        
        # Optionally store the result (without upload references)
        if data.get('save_result', False):
            db = get_db()
            comparisons_collection = db.comparisons
            
            comparison_record = {
                'comparison_type': 'simple_text_only',
                'source_text': source_text,
                'destination_text': destination_text,
                'comparison_date': datetime.utcnow(),
                'validation_result': {
                    'overall_similarity': validation_result.overall_similarity,
                    'total_lines': validation_result.total_lines,
                    'matched_lines': validation_result.matched_lines,
                    'missing_lines': validation_result.missing_lines,
                    'extra_lines': validation_result.extra_lines,
                    'character_accuracy': validation_result.character_accuracy,
                    'word_accuracy': validation_result.word_accuracy,
                    'text_matches': [
                        {
                            'source_text': tm.source_text,
                            'dest_text': tm.dest_text,
                            'match_score': tm.match_score,
                            'match_type': tm.match_type,
                            'line_number': tm.line_number,
                            'issues': tm.issues
                        } for tm in validation_result.text_matches
                    ],
                    'recommendations': validation_result.recommendations
                }
            }
            
            result = comparisons_collection.insert_one(comparison_record)
            comparison_id = str(result.inserted_id)
        else:
            comparison_id = None
        
        logger.info(f"Direct text comparison completed with overall similarity: {validation_result.overall_similarity:.1f}%")
        
        return jsonify({
            'success': True,
            'comparison_id': comparison_id,
            'validation_result': {
                'overall_similarity': round(validation_result.overall_similarity, 1),
                'total_lines': validation_result.total_lines,
                'matched_lines': validation_result.matched_lines,
                'missing_lines': validation_result.missing_lines,
                'extra_lines': validation_result.extra_lines,
                'character_accuracy': round(validation_result.character_accuracy, 1),
                'word_accuracy': round(validation_result.word_accuracy, 1),
                'text_matches': [
                    {
                        'source_text': tm.source_text,
                        'dest_text': tm.dest_text,
                        'match_score': round(tm.match_score, 1),
                        'match_type': tm.match_type,
                        'line_number': tm.line_number,
                        'issues': tm.issues
                    } for tm in validation_result.text_matches
                ],
                'recommendations': validation_result.recommendations
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Direct text comparison error: {str(e)}")
        return jsonify({
            'error': 'Comparison failed',
            'details': str(e)
        }), 500

@simple_validation_bp.route('/history', methods=['GET'])
def get_comparison_history():
    """
    Get comparison history with pagination
    Query params: page (default 1), limit (default 20)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        db = get_db()
        comparisons_collection = db.comparisons
        
        # Get total count
        total = comparisons_collection.count_documents({})
        
        # Get paginated results
        comparisons = comparisons_collection.find({}).sort('comparison_date', -1).skip((page - 1) * limit).limit(limit)
        
        comparison_list = []
        for comp in comparisons:
            validation_result = comp.get('validation_result', {})
            comparison_list.append({
                'comparison_id': str(comp['_id']),
                'comparison_date': comp['comparison_date'].isoformat(),
                'overall_similarity': validation_result.get('overall_similarity', 0),
                'total_lines': validation_result.get('total_lines', 0),
                'matched_lines': validation_result.get('matched_lines', 0),
                'comparison_type': comp.get('comparison_type', 'simple_text'),
                'main_upload_id': str(comp['main_upload_id']) if 'main_upload_id' in comp else None,
                'secondary_upload_id': str(comp['secondary_upload_id']) if 'secondary_upload_id' in comp else None
            })
        
        return jsonify({
            'success': True,
            'comparisons': comparison_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get comparison history error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve comparison history'}), 500

@simple_validation_bp.route('/result/<comparison_id>', methods=['GET'])
def get_comparison_result(comparison_id):
    """Get detailed comparison result by ID"""
    try:
        db = get_db()
        comparisons_collection = db.comparisons
        
        comparison = comparisons_collection.find_one({'_id': ObjectId(comparison_id)})
        if not comparison:
            return jsonify({'error': 'Comparison result not found'}), 404
        
        return jsonify({
            'success': True,
            'comparison_id': comparison_id,
            'comparison_date': comparison['comparison_date'].isoformat(),
            'comparison_type': comparison.get('comparison_type', 'simple_text'),
            'main_upload_id': str(comparison['main_upload_id']) if 'main_upload_id' in comparison else None,
            'secondary_upload_id': str(comparison['secondary_upload_id']) if 'secondary_upload_id' in comparison else None,
            'validation_result': comparison['validation_result']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get comparison result error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve comparison result'}), 500