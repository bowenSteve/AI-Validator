from flask import Blueprint, request, jsonify, current_app, Response
from datetime import datetime, timedelta
import uuid
import os
import base64
from werkzeug.utils import secure_filename
import magic
from PIL import Image
import io
import logging

# Import SQLAlchemy models
from models import db, Upload

# Import Gemini service
from services.gemini import gemini_service

uploads_bp = Blueprint('Uploads', __name__, url_prefix='/api/uploads')
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file_data):
    """Validate if the uploaded data is actually an image"""
    try:
        # Check file signature using python-magic
        mime_type = magic.from_buffer(file_data, mime=True)
        return mime_type.startswith('image/')
    except:
        return False

def optimize_image(file_data, max_size=(1920, 1080), quality=85):
    """Optimize image size and quality"""
    try:
        image = Image.open(io.BytesIO(file_data))
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Resize if larger than max_size
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except:
        return file_data  # Return original if optimization fails

def handle_image_upload(file_data, filename, content_type, image_type):
    """Common function to handle image upload logic with Gemini processing"""
    # Validate file size (10MB limit)
    if len(file_data) > 10 * 1024 * 1024:
        raise ValueError('File size exceeds 10MB limit')

    # Validate if it's actually an image
    if not validate_image(file_data):
        raise ValueError('Invalid image file')

    # Optimize image
    optimized_data = optimize_image(file_data)

    # Generate unique filename
    secure_name = secure_filename(filename)
    unique_filename = f"{uuid.uuid4()}_{secure_name}"

    # Process with Gemini API
    logger.info(f"Triggering Gemini API call for {image_type} image processing")
    gemini_success, gemini_result = gemini_service.extract_text_from_image(optimized_data, image_type)

    # Create new upload record
    upload = Upload(
        filename=unique_filename,
        original_filename=filename,
        image_type=image_type,
        content_type=content_type,
        file_size=len(optimized_data),
        original_size=len(file_data),
        file_data=optimized_data,
        upload_date=datetime.utcnow(),
        status='uploaded',
        gemini_processed=gemini_success,
        gemini_processed_at=datetime.utcnow() if gemini_success else None,
        gemini_extracted_text=gemini_result.get('extracted_text', '') if gemini_success else None,
        gemini_confidence_score=gemini_result.get('confidence_score', 0.0) if gemini_success else 0.0,
        gemini_has_uncertainties=gemini_result.get('has_uncertainties', False) if gemini_success else False,
        gemini_validation=gemini_result.get('validation', {}) if gemini_success else {},
        gemini_result=gemini_result,
        gemini_error=gemini_result.get('error') if not gemini_success else None
    )

    # Save to database
    db.session.add(upload)
    db.session.commit()

    # Prepare response
    response_data = {
        'upload_id': str(upload.id),
        'filename': unique_filename,
        'image_type': image_type,
        'file_size': len(optimized_data),
        'upload_date': upload.upload_date.isoformat(),
        'gemini_processing': {
            'success': gemini_success,
            'extracted_text': gemini_result.get('extracted_text', '') if gemini_success else None,
            'confidence_score': gemini_result.get('confidence_score', 0.0) if gemini_success else 0.0,
            'has_uncertainties': gemini_result.get('has_uncertainties', False) if gemini_success else False,
            'validation': gemini_result.get('validation', {}) if gemini_success else {},
            'error': gemini_result.get('error') if not gemini_success else None,
            'processing_time': gemini_result.get('attempt', 1) if gemini_success else None
        }
    }

    # Log the result
    if gemini_success:
        logger.info(f"Successfully processed {image_type} image with Gemini. Text length: {len(gemini_result.get('extracted_text', ''))}")
    else:
        logger.error(f"Failed to process {image_type} image with Gemini: {gemini_result.get('error', 'Unknown error')}")

    return response_data

# ============= MAIN IMAGE ROUTES =============

@uploads_bp.route('/main/upload', methods=['POST'])
def upload_main_image():
    """
    Upload main screenshot via form data
    Expects: multipart/form-data with 'image' file
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only images are allowed'}), 400
        
        # Read file data
        file_data = file.read()
        
        logger.info(f"File received: {file.filename} ({len(file_data)} bytes) for main upload")
        
        # Handle upload
        result = handle_image_upload(file_data, file.filename, file.content_type, 'main')
        
        return jsonify({
            'success': True,
            'message': 'Main image uploaded successfully',
            **result
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Main image upload error: {str(e)}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@uploads_bp.route('/main/upload/base64', methods=['POST'])
def upload_main_image_base64():
    """
    Upload main screenshot from base64 data (paste functionality)
    Expects: JSON with 'image_data' (base64 string) and optional 'filename'
    """
    try:
        data = request.get_json()
        
        if not data or 'image_data' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        image_data = data['image_data']
        filename = data.get('filename', f'main-screenshot-{int(datetime.utcnow().timestamp())}.png')
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        try:
            file_data = base64.b64decode(image_data)
            logger.info(f"Base64 file received: {filename} ({len(file_data)} bytes) for main upload")
        except Exception:
            return jsonify({'error': 'Invalid base64 image data'}), 400
        
        # Handle upload
        result = handle_image_upload(file_data, filename, 'image/png', 'main')
        
        return jsonify({
            'success': True,
            'message': 'Main image uploaded successfully',
            **result
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Main image base64 upload error: {str(e)}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@uploads_bp.route('/main/list', methods=['GET'])
def get_main_images():
    """
    Get list of main images with pagination
    Query params: page (default 1), limit (default 20)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))

        # Query only main images
        total = Upload.query.filter_by(image_type='main').count()

        # Get paginated results
        uploads = Upload.query.filter_by(image_type='main')\
            .order_by(Upload.upload_date.desc())\
            .offset((page - 1) * limit)\
            .limit(limit)\
            .all()

        upload_list = []
        for upload in uploads:
            upload_list.append({
                'upload_id': str(upload.id),
                'filename': upload.original_filename,
                'file_size': upload.file_size,
                'upload_date': upload.upload_date.isoformat(),
                'status': upload.status
            })

        return jsonify({
            'success': True,
            'images': upload_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get main images error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve main images'}), 500

@uploads_bp.route('/main/<upload_id>', methods=['DELETE'])
def delete_main_image(upload_id):
    """Delete a main image and its associated file"""
    try:
        # Find the upload record (ensure it's a main image)
        upload = Upload.query.filter_by(id=upload_id, image_type='main').first()

        if not upload:
            return jsonify({'error': 'Main image not found'}), 404

        # Delete upload record (file data is stored in the record itself)
        db.session.delete(upload)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Main image deleted successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Delete main image error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete main image'}), 500

# ============= SECONDARY IMAGE ROUTES =============

@uploads_bp.route('/secondary/upload', methods=['POST'])
def upload_secondary_image():
    """
    Upload secondary screenshot via form data
    Expects: multipart/form-data with 'image' file
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only images are allowed'}), 400
        
        # Read file data
        file_data = file.read()
        
        logger.info(f"File received: {file.filename} ({len(file_data)} bytes) for secondary upload")
        
        # Handle upload
        result = handle_image_upload(file_data, file.filename, file.content_type, 'secondary')
        
        return jsonify({
            'success': True,
            'message': 'Secondary image uploaded successfully',
            **result
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Secondary image upload error: {str(e)}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@uploads_bp.route('/secondary/upload/base64', methods=['POST'])
def upload_secondary_image_base64():
    """
    Upload secondary screenshot from base64 data (paste functionality)
    Expects: JSON with 'image_data' (base64 string) and optional 'filename'
    """
    try:
        data = request.get_json()
        
        if not data or 'image_data' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        image_data = data['image_data']
        filename = data.get('filename', f'secondary-screenshot-{int(datetime.utcnow().timestamp())}.png')
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        try:
            file_data = base64.b64decode(image_data)
            logger.info(f"Base64 file received: {filename} ({len(file_data)} bytes) for secondary upload")
        except Exception:
            return jsonify({'error': 'Invalid base64 image data'}), 400
        
        # Handle upload
        result = handle_image_upload(file_data, filename, 'image/png', 'secondary')
        
        return jsonify({
            'success': True,
            'message': 'Secondary image uploaded successfully',
            **result
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Secondary image base64 upload error: {str(e)}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@uploads_bp.route('/secondary/list', methods=['GET'])
def get_secondary_images():
    """
    Get list of secondary images with pagination
    Query params: page (default 1), limit (default 20)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))

        # Query only secondary images
        total = Upload.query.filter_by(image_type='secondary').count()

        # Get paginated results
        uploads = Upload.query.filter_by(image_type='secondary')\
            .order_by(Upload.upload_date.desc())\
            .offset((page - 1) * limit)\
            .limit(limit)\
            .all()

        upload_list = []
        for upload in uploads:
            upload_list.append({
                'upload_id': str(upload.id),
                'filename': upload.original_filename,
                'file_size': upload.file_size,
                'upload_date': upload.upload_date.isoformat(),
                'status': upload.status
            })

        return jsonify({
            'success': True,
            'images': upload_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get secondary images error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve secondary images'}), 500

@uploads_bp.route('/secondary/<upload_id>', methods=['DELETE'])
def delete_secondary_image(upload_id):
    """Delete a secondary image and its associated file"""
    try:
        # Find the upload record (ensure it's a secondary image)
        upload = Upload.query.filter_by(id=upload_id, image_type='secondary').first()

        if not upload:
            return jsonify({'error': 'Secondary image not found'}), 404

        # Delete upload record (file data is stored in the record itself)
        db.session.delete(upload)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Secondary image deleted successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Delete secondary image error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete secondary image'}), 500



# ============= TEXT EXTRACTION ROUTES =============

@uploads_bp.route('/text/<upload_id>', methods=['GET'])
def get_extracted_text(upload_id):
    """
    Get extracted text for a specific upload
    """
    try:
        upload = Upload.query.filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'image_type': upload.image_type,
            'filename': upload.original_filename,
            'extracted_text': upload.gemini_extracted_text or '',
            'confidence_score': upload.gemini_confidence_score or 0.0,
            'has_uncertainties': upload.gemini_has_uncertainties or False,
            'processing_success': upload.gemini_processed or False,
            'processed_at': upload.gemini_processed_at.isoformat() if upload.gemini_processed_at else None,
            'error': upload.gemini_error
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get extracted text error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve extracted text'}), 500

@uploads_bp.route('/reprocess/<upload_id>', methods=['POST'])
def reprocess_with_gemini(upload_id):
    """
    Reprocess an upload with Gemini API (useful for failed attempts)
    """
    try:
        upload = Upload.query.filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        # Reprocess with Gemini
        logger.info(f"Triggering Gemini API call for reprocessing {upload.image_type} image")
        gemini_success, gemini_result = gemini_service.extract_text_from_image(
            upload.file_data,
            upload.image_type
        )

        # Update upload record
        upload.gemini_processed = gemini_success
        upload.gemini_processed_at = datetime.utcnow() if gemini_success else None
        upload.gemini_result = gemini_result
        upload.gemini_extracted_text = gemini_result.get('extracted_text', '') if gemini_success else None
        upload.gemini_confidence_score = gemini_result.get('confidence_score', 0.0) if gemini_success else 0.0
        upload.gemini_has_uncertainties = gemini_result.get('has_uncertainties', False) if gemini_success else False
        upload.gemini_validation = gemini_result.get('validation', {}) if gemini_success else {}
        upload.gemini_error = gemini_result.get('error') if not gemini_success else None
        upload.gemini_reprocessed_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'reprocessing_success': gemini_success,
            'extracted_text': gemini_result.get('extracted_text', '') if gemini_success else None,
            'confidence_score': gemini_result.get('confidence_score', 0.0) if gemini_success else 0.0,
            'has_uncertainties': gemini_result.get('has_uncertainties', False) if gemini_success else False,
            'validation': gemini_result.get('validation', {}) if gemini_success else {},
            'error': gemini_result.get('error') if not gemini_success else None,
            'reprocessed_at': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Reprocess error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Reprocessing failed', 'details': str(e)}), 500

@uploads_bp.route('/image/<upload_id>', methods=['GET'])
def get_image(upload_id):
    """
    Retrieve an image by upload_id (works for both main and secondary)
    Returns the actual image file
    """
    try:
        upload = Upload.query.filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'error': 'Image not found'}), 404

        response = Response(
            upload.file_data,
            mimetype=upload.content_type or 'image/jpeg'
        )

        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year cache
        response.headers['Content-Disposition'] = f'inline; filename="{upload.filename}"'

        return response

    except Exception as e:
        current_app.logger.error(f"Image retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve image'}), 500

@uploads_bp.route('/all', methods=['GET'])
def get_all_uploads():
    """
    Get list of all uploads (both main and secondary) with pagination
    Query params: page (default 1), limit (default 20), type (optional filter)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        image_type = request.args.get('type')  # Optional filter: 'main' or 'secondary'

        # Build query
        query = Upload.query
        if image_type and image_type in ['main', 'secondary']:
            query = query.filter_by(image_type=image_type)

        # Get total count
        total = query.count()

        # Get paginated results
        uploads = query.order_by(Upload.upload_date.desc())\
            .offset((page - 1) * limit)\
            .limit(limit)\
            .all()

        upload_list = []
        for upload in uploads:
            upload_list.append({
                'upload_id': str(upload.id),
                'filename': upload.original_filename,
                'image_type': upload.image_type,
                'file_size': upload.file_size,
                'upload_date': upload.upload_date.isoformat(),
                'status': upload.status
            })

        return jsonify({
            'success': True,
            'uploads': upload_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get all uploads error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve uploads'}), 500