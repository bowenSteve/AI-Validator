from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import pymongo
from bson import ObjectId
import uuid
import os
import base64
import gridfs
from werkzeug.utils import secure_filename
import magic
from PIL import Image
import io

uploads_bp = Blueprint('Uploads', __name__, url_prefix='/api/uploads')

def get_db():
    client = pymongo.MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    return client[os.getenv('MONGODB_DB_NAME', 'middesk')]

def get_gridfs():
    """Get GridFS instance for storing large files"""
    db = get_db()
    return gridfs.GridFS(db)

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
    """Common function to handle image upload logic"""
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
    
    # Store in GridFS
    fs = get_gridfs()
    file_id = fs.put(
        optimized_data,
        filename=unique_filename,
        content_type=content_type,
        upload_date=datetime.utcnow(),
        metadata={
            'original_filename': filename,
            'image_type': image_type,
            'file_size': len(optimized_data),
            'original_size': len(file_data)
        }
    )
    
    # Store metadata in uploads collection
    db = get_db()
    uploads_collection = db.uploads
    
    upload_record = {
        'file_id': file_id,
        'filename': unique_filename,
        'original_filename': filename,
        'image_type': image_type,
        'content_type': content_type,
        'file_size': len(optimized_data),
        'original_size': len(file_data),
        'upload_date': datetime.utcnow(),
        'status': 'uploaded'
    }
    
    result = uploads_collection.insert_one(upload_record)
    
    return {
        'upload_id': str(result.inserted_id),
        'file_id': str(file_id),
        'filename': unique_filename,
        'image_type': image_type,
        'file_size': len(optimized_data),
        'upload_date': upload_record['upload_date'].isoformat()
    }

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
        
        db = get_db()
        uploads_collection = db.uploads
        
        # Query only main images
        query = {'image_type': 'main'}
        
        # Get total count
        total = uploads_collection.count_documents(query)
        
        # Get paginated results
        uploads = uploads_collection.find(query).sort('upload_date', -1).skip((page - 1) * limit).limit(limit)
        
        upload_list = []
        for upload in uploads:
            upload_list.append({
                'upload_id': str(upload['_id']),
                'file_id': str(upload['file_id']),
                'filename': upload['original_filename'],
                'file_size': upload['file_size'],
                'upload_date': upload['upload_date'].isoformat(),
                'status': upload['status']
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
        db = get_db()
        uploads_collection = db.uploads
        
        # Find the upload record (ensure it's a main image)
        upload = uploads_collection.find_one({
            '_id': ObjectId(upload_id),
            'image_type': 'main'
        })
        
        if not upload:
            return jsonify({'error': 'Main image not found'}), 404
        
        # Delete from GridFS
        fs = get_gridfs()
        try:
            fs.delete(upload['file_id'])
        except gridfs.NoFile:
            pass  # File already deleted
        
        # Delete upload record
        uploads_collection.delete_one({'_id': ObjectId(upload_id)})
        
        return jsonify({
            'success': True,
            'message': 'Main image deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete main image error: {str(e)}")
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
        
        db = get_db()
        uploads_collection = db.uploads
        
        # Query only secondary images
        query = {'image_type': 'secondary'}
        
        # Get total count
        total = uploads_collection.count_documents(query)
        
        # Get paginated results
        uploads = uploads_collection.find(query).sort('upload_date', -1).skip((page - 1) * limit).limit(limit)
        
        upload_list = []
        for upload in uploads:
            upload_list.append({
                'upload_id': str(upload['_id']),
                'file_id': str(upload['file_id']),
                'filename': upload['original_filename'],
                'file_size': upload['file_size'],
                'upload_date': upload['upload_date'].isoformat(),
                'status': upload['status']
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
        db = get_db()
        uploads_collection = db.uploads
        
        # Find the upload record (ensure it's a secondary image)
        upload = uploads_collection.find_one({
            '_id': ObjectId(upload_id),
            'image_type': 'secondary'
        })
        
        if not upload:
            return jsonify({'error': 'Secondary image not found'}), 404
        
        # Delete from GridFS
        fs = get_gridfs()
        try:
            fs.delete(upload['file_id'])
        except gridfs.NoFile:
            pass  # File already deleted
        
        # Delete upload record
        uploads_collection.delete_one({'_id': ObjectId(upload_id)})
        
        return jsonify({
            'success': True,
            'message': 'Secondary image deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete secondary image error: {str(e)}")
        return jsonify({'error': 'Failed to delete secondary image'}), 500



# ============= SHARED ROUTES =============

@uploads_bp.route('/image/<file_id>', methods=['GET'])
def get_image(file_id):
    """
    Retrieve an image by file_id (works for both main and secondary)
    Returns the actual image file
    """
    try:
        fs = get_gridfs()
        
        try:
            grid_out = fs.get(ObjectId(file_id))
        except gridfs.NoFile:
            return jsonify({'error': 'Image not found'}), 404
        
        response = current_app.response_class(
            grid_out.read(),
            mimetype=grid_out.content_type or 'image/jpeg'
        )
        
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year cache
        response.headers['Content-Disposition'] = f'inline; filename="{grid_out.filename}"'
        
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
        query = {}
        if image_type and image_type in ['main', 'secondary']:
            query['image_type'] = image_type
        
        db = get_db()
        uploads_collection = db.uploads
        
        # Get total count
        total = uploads_collection.count_documents(query)
        
        # Get paginated results
        uploads = uploads_collection.find(query).sort('upload_date', -1).skip((page - 1) * limit).limit(limit)
        
        upload_list = []
        for upload in uploads:
            upload_list.append({
                'upload_id': str(upload['_id']),
                'file_id': str(upload['file_id']),
                'filename': upload['original_filename'],
                'image_type': upload['image_type'],
                'file_size': upload['file_size'],
                'upload_date': upload['upload_date'].isoformat(),
                'status': upload['status']
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