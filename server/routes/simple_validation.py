from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import os

# Import SQLAlchemy models
from models import db, Upload, Comparison

# Import our simple text comparison service
from services.simple_text_comparison import simple_text_comparison
from services.gemini_validator import gemini_validator

simple_validation_bp = Blueprint('SimpleValidation', __name__, url_prefix='/api/validation')
logger = logging.getLogger(__name__)


@simple_validation_bp.route('/compare/gemini', methods=['POST'])
def compare_uploads_with_gemini():
    """
    Compare uploaded images using Gemini AI for intelligent validation
    Expects: JSON with 'main_upload_ids' and 'secondary_upload_ids' (arrays)
    """
    try:
        data = request.get_json()
        
        if not data or 'main_upload_ids' not in data or 'secondary_upload_ids' not in data:
            return jsonify({
                'error': 'Both main_upload_ids and secondary_upload_ids arrays are required'
            }), 400
        
        main_upload_ids = data['main_upload_ids']
        secondary_upload_ids = data['secondary_upload_ids']
        
        if not isinstance(main_upload_ids, list) or not isinstance(secondary_upload_ids, list):
            return jsonify({
                'error': 'upload_ids must be arrays'
            }), 400
        
        # Fetch and combine text from main images
        main_combined_text = ""
        for upload_id in main_upload_ids:
            upload = Upload.query.filter_by(id=upload_id, image_type='main').first()
            if upload and upload.gemini_extracted_text:
                main_combined_text += upload.gemini_extracted_text + "\n\n"

        # Fetch and combine text from secondary images
        secondary_combined_text = ""
        for upload_id in secondary_upload_ids:
            upload = Upload.query.filter_by(id=upload_id, image_type='secondary').first()
            if upload and upload.gemini_extracted_text:
                secondary_combined_text += upload.gemini_extracted_text + "\n\n"
        
        # Validation checks
        if not main_combined_text.strip():
            return jsonify({
                'error': 'No text extracted from main images. Please ensure images were processed successfully.'
            }), 400
        
        if not secondary_combined_text.strip():
            return jsonify({
                'error': 'No text extracted from secondary images. Please ensure images were processed successfully.'
            }), 400
        
        logger.info(f"Starting Gemini validation with {len(main_upload_ids)} main images and {len(secondary_upload_ids)} secondary images")
        
        # Perform Gemini validation with combined text
        success, validation_result = gemini_validator.validate_data_transfer(
            main_combined_text.strip(), 
            secondary_combined_text.strip()
        )
        
        if not success:
            return jsonify({
                'error': 'Gemini validation failed',
                'details': validation_result.get('error', 'Unknown error')
            }), 500
        
        # Store comparison result
        comparison = Comparison(
            main_upload_ids=main_upload_ids,
            secondary_upload_ids=secondary_upload_ids,
            comparison_date=datetime.utcnow(),
            comparison_type='gemini_validation_multi',
            validation_result=validation_result
        )

        db.session.add(comparison)
        db.session.commit()
        
        logger.info(f"Multi-image Gemini validation completed with accuracy: {validation_result.get('accuracy_score', 0)}%")
        
        return jsonify({
            'success': True,
            'comparison_id': str(comparison.id),
            'validation_result': validation_result,
            'images_processed': {
                'main_count': len(main_upload_ids),
                'secondary_count': len(secondary_upload_ids)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Multi-image Gemini validation error: {str(e)}")
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
        main_upload = Upload.query.filter_by(id=main_upload_id, image_type='main').first()
        secondary_upload = Upload.query.filter_by(id=secondary_upload_id, image_type='secondary').first()

        if not main_upload:
            return jsonify({'error': 'Main upload not found'}), 404

        if not secondary_upload:
            return jsonify({'error': 'Secondary upload not found'}), 404

        # Extract the text from both uploads
        main_text = main_upload.gemini_extracted_text or ''
        secondary_text = secondary_upload.gemini_extracted_text or ''
        
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
        validation_dict = {
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

        comparison = Comparison(
            main_upload_id=main_upload_id,
            secondary_upload_id=secondary_upload_id,
            comparison_date=datetime.utcnow(),
            comparison_type='simple_text',
            validation_result=validation_dict
        )

        db.session.add(comparison)
        db.session.commit()
        
        logger.info(f"Text comparison completed with overall similarity: {validation_result.overall_similarity:.1f}%")
        
        return jsonify({
            'success': True,
            'comparison_id': str(comparison.id),
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
            validation_dict = {
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

            comparison = Comparison(
                comparison_type='simple_text_only',
                source_text=source_text,
                destination_text=destination_text,
                comparison_date=datetime.utcnow(),
                validation_result=validation_dict
            )

            db.session.add(comparison)
            db.session.commit()
            comparison_id = str(comparison.id)
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
        
        # Get total count
        total = Comparison.query.count()

        # Get paginated results
        comparisons = Comparison.query.order_by(Comparison.comparison_date.desc())\
            .offset((page - 1) * limit)\
            .limit(limit)\
            .all()

        comparison_list = []
        for comp in comparisons:
            validation_result = comp.validation_result or {}
            comparison_list.append({
                'comparison_id': str(comp.id),
                'comparison_date': comp.comparison_date.isoformat(),
                'overall_similarity': validation_result.get('overall_similarity', 0),
                'total_lines': validation_result.get('total_lines', 0),
                'matched_lines': validation_result.get('matched_lines', 0),
                'comparison_type': comp.comparison_type,
                'main_upload_id': str(comp.main_upload_id) if comp.main_upload_id else None,
                'secondary_upload_id': str(comp.secondary_upload_id) if comp.secondary_upload_id else None
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
        comparison = Comparison.query.filter_by(id=comparison_id).first()
        if not comparison:
            return jsonify({'error': 'Comparison result not found'}), 404

        return jsonify({
            'success': True,
            'comparison_id': comparison_id,
            'comparison_date': comparison.comparison_date.isoformat(),
            'comparison_type': comparison.comparison_type,
            'main_upload_id': str(comparison.main_upload_id) if comparison.main_upload_id else None,
            'secondary_upload_id': str(comparison.secondary_upload_id) if comparison.secondary_upload_id else None,
            'validation_result': comparison.validation_result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get comparison result error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve comparison result'}), 500

@simple_validation_bp.route('/result/<comparison_id>', methods=['DELETE'])
def delete_comparison_result(comparison_id):
    """Delete a comparison result by ID"""
    try:
        # Find the comparison
        comparison = Comparison.query.filter_by(id=comparison_id).first()
        if not comparison:
            return jsonify({'error': 'Comparison result not found'}), 404

        # Delete the comparison record
        db.session.delete(comparison)
        db.session.commit()
        
        logger.info(f"Deleted comparison result: {comparison_id}")
        
        return jsonify({
            'success': True,
            'message': 'Comparison result deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete comparison result error: {str(e)}")
        return jsonify({'error': 'Failed to delete comparison result'}), 500