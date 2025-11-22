"""
Wedding Gallery Uploader - Flask Application

A secure web application for collecting and sharing wedding photos and videos.
Allows guests to upload media files which are displayed in a responsive gallery.

Features:
- Multi-file upload with drag-and-drop
- Automatic thumbnail generation
- File validation and security checks
- Real client IP detection (CloudFlare support)
- Responsive gallery with fullscreen preview

Author: Wedding Uploader Contributors
License: MIT
"""

import os
import logging
import magic
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import uuid
from datetime import datetime
from PIL import Image
import io
import hashlib
import ipaddress
from werkzeug.serving import WSGIRequestHandler

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Add middleware to log real IPs
@app.before_request
def log_real_ip():
    """Log requests with real client IP"""
    real_ip = get_real_client_ip()
    app.logger.info(f'{real_ip} - {request.method} {request.path} - User-Agent: {request.headers.get("User-Agent", "Unknown")}')

def get_real_client_ip():
    """Extract real client IP from CloudFlare headers or fallback to direct connection (IPv4 preferred)"""

    def is_ipv6(ip_str: str) -> bool:
        """Check if IP string is IPv6"""
        try:
            addr = ipaddress.ip_address(ip_str)
            return addr.version == 6
        except:
            return False

    def simplify_ipv6(ip_str: str) -> str:
        """Convert IPv6 to short form for cleaner display"""
        try:
            addr = ipaddress.ip_address(ip_str)
            if addr.version == 6:
                # Check if it's IPv4-mapped IPv6 (::ffff:192.168.1.1)
                if ip_str.startswith("::ffff:"):
                    return ip_str.replace("::ffff:", "")
                # Return compressed IPv6 format
                return addr.compressed
            return ip_str
        except:
            return ip_str

    def extract_best_ip(ip_list: str) -> str:
        """Extract best IP from comma-separated list (prefer IPv4, simplify IPv6)"""
        if not ip_list:
            return "unknown"

        ips = [ip.strip() for ip in ip_list.split(",")]

        # First pass: look for IPv4
        for ip in ips:
            if ip and not is_ipv6(ip):
                return ip

        # Second pass: if only IPv6, return first one simplified
        for ip in ips:
            if ip:
                return simplify_ipv6(ip)

        return "unknown"

    # CloudFlare IPv6 header (real IPv6 if present - CloudFlare Pseudo IPv4 feature)
    # Check this FIRST because CF-Connecting-IP might contain fake pseudo IPv4
    cf_ipv6 = request.headers.get("CF-Connecting-IPv6")
    cf_pseudo_ipv4 = request.headers.get("CF-Pseudo-IPv4")

    if cf_ipv6:
        result = simplify_ipv6(cf_ipv6)
        if cf_pseudo_ipv4:
            app.logger.debug(f"[IP Detection] CF-Connecting-IPv6: {cf_ipv6} -> {result} (Pseudo IPv4: {cf_pseudo_ipv4})")
        else:
            app.logger.debug(f"[IP Detection] CF-Connecting-IPv6: {cf_ipv6} -> {result}")
        return result

    # CloudFlare passes real IP in CF-Connecting-IP header
    # Note: This might be pseudo IPv4 (Class E: 240.0.0.0/4) if user is on IPv6
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        result = extract_best_ip(cf_ip)
        # Check if it's a pseudo IPv4 (Class E starts with 240-255)
        if result.startswith(("240.", "241.", "242.", "243.", "244.", "245.", "246.", "247.",
                              "248.", "249.", "250.", "251.", "252.", "253.", "254.", "255.")):
            app.logger.debug(f"[IP Detection] CF-Connecting-IP: {cf_ip} (Pseudo IPv4 - real IPv6 not provided)")
        else:
            app.logger.debug(f"[IP Detection] CF-Connecting-IP: {cf_ip} -> {result}")
        return result

    # X-Forwarded-For as fallback for other proxies
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        result = extract_best_ip(x_forwarded)
        app.logger.debug(f"[IP Detection] X-Forwarded-For: {x_forwarded} -> {result}")
        return result

    # X-Real-IP as another fallback
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        result = extract_best_ip(x_real_ip)
        app.logger.debug(f"[IP Detection] X-Real-IP: {x_real_ip} -> {result}")
        return result

    # Direct connection IP (no proxy)
    client_ip = request.remote_addr
    if client_ip:
        result = simplify_ipv6(client_ip)
        app.logger.debug(f"[IP Detection] Direct connection: {client_ip} -> {result}")
        return result

    app.logger.debug("[IP Detection] No IP found, returning unknown")
    return "unknown"

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self';"
    return response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# Error handlers
@app.errorhandler(413)
def too_large(e):
    app.logger.warning(f'File too large from {get_real_client_ip()}')
    return "File too large. Maximum size is 50MB.", 413

# Rate limiting removed - no 429 handler needed

@app.errorhandler(400)
def bad_request(e):
    app.logger.warning(f'Bad request from {get_real_client_ip()}: {str(e)}')
    return "Bad request", 400

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

# Storage directories
UPLOAD_FOLDER = 'uploads'  # Original uploaded files
THUMBNAIL_FOLDER = 'thumbnails'  # Generated thumbnail images

# File type restrictions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_MIMETYPES = {
    # Image formats
    'image/png', 'image/jpeg', 'image/jpg', 'image/gif',
    # Video formats
    'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'
}

# Upload limits
MAX_FILES_PER_REQUEST = 10  # Maximum files per upload request
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file

# Thumbnail settings
THUMBNAIL_SIZE = (300, 300)  # Square thumbnails with white background

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(THUMBNAIL_FOLDER):
    os.makedirs(THUMBNAIL_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed.

    Args:
        filename (str): Name of the file to check

    Returns:
        bool: True if file extension is in ALLOWED_EXTENSIONS
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_content(file_path, filename):
    """Validate file content using MIME type detection and image verification.

    Performs multi-layer validation:
    1. MIME type check using python-magic
    2. Image integrity check using PIL for image files

    Args:
        file_path (str): Path to the uploaded file
        filename (str): Original filename for logging

    Returns:
        bool: True if file passes all validation checks
    """
    try:
        # Check MIME type
        mime_type = magic.from_file(file_path, mime=True)
        if mime_type not in ALLOWED_MIMETYPES:
            app.logger.warning(f'Invalid MIME type {mime_type} for file {filename}')
            return False

        # Additional checks for images
        if mime_type.startswith('image/'):
            try:
                with Image.open(file_path) as img:
                    img.verify()  # Verify it's a valid image
                return True
            except Exception as e:
                app.logger.warning(f'Invalid image file {filename}: {str(e)}')
                return False

        # For videos, just check MIME type is sufficient
        if mime_type.startswith('video/'):
            return True

        return False
    except Exception as e:
        app.logger.error(f'Error validating file {filename}: {str(e)}')
        return False

def get_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_type(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    if extension in {'png', 'jpg', 'jpeg', 'gif'}:
        return 'image'
    elif extension in {'mp4', 'mov', 'avi', 'mkv', 'webm'}:
        return 'video'
    return 'unknown'

def create_thumbnail(image_path, thumbnail_path):
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Create thumbnail maintaining aspect ratio
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # Create a square thumbnail with white background
            thumb = Image.new('RGB', THUMBNAIL_SIZE, (255, 255, 255))
            # Center the image
            x = (THUMBNAIL_SIZE[0] - img.size[0]) // 2
            y = (THUMBNAIL_SIZE[1] - img.size[1]) // 2
            thumb.paste(img, (x, y))

            # Save as JPEG for smaller file size
            thumb.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"Error creating thumbnail for {image_path}: {str(e)}")
        return False
    return False

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page - displays the upload form and gallery."""
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if allowed_file(filename):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_type = get_file_type(filename)

            # Check if thumbnail exists for images
            has_thumbnail = False
            thumbnail_name = None
            if file_type == 'image':
                thumbnail_name = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"
                thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_name)
                has_thumbnail = os.path.exists(thumbnail_path)

            file_info = {
                'name': filename,
                'type': file_type,
                'upload_time': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M'),
                'has_thumbnail': has_thumbnail,
                'thumbnail_name': thumbnail_name
            }
            files.append(file_info)

    # Sort by most recent first
    files.sort(key=lambda x: x['upload_time'], reverse=True)
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload requests.

    Accepts multiple files (up to MAX_FILES_PER_REQUEST), validates them,
    generates thumbnails for images, and saves them to disk.

    Returns:
        Redirect to index page with flash messages indicating success/failure
    """
    if 'files' not in request.files:
        app.logger.warning(f'No files in upload request from {get_real_client_ip()}')
        flash('No files selected')
        return redirect(request.url)

    files = request.files.getlist('files')

    # Security: Limit number of files per request
    if len(files) > MAX_FILES_PER_REQUEST:
        app.logger.warning(f'Too many files uploaded from {get_real_client_ip()}: {len(files)}')
        flash(f'Too many files. Maximum {MAX_FILES_PER_REQUEST} files per upload.')
        return redirect(request.url)

    uploaded_count = 0
    failed_count = 0

    for file in files:
        if file and file.filename != '':
            # Sanitize filename
            original_filename = secure_filename(file.filename)
            if not original_filename:
                app.logger.warning(f'Invalid filename from {get_real_client_ip()}: {file.filename}')
                failed_count += 1
                continue

            if not allowed_file(original_filename):
                app.logger.warning(f'Disallowed file type from {get_real_client_ip()}: {original_filename}')
                flash(f'File type not allowed: {original_filename}')
                failed_count += 1
                continue

            # Generate unique filename to prevent conflicts
            filename = f"{uuid.uuid4().hex}_{original_filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                # Save file temporarily
                file.save(file_path)

                # Validate file content and MIME type
                if not validate_file_content(file_path, original_filename):
                    os.remove(file_path)  # Remove invalid file
                    flash(f'Invalid or potentially dangerous file: {original_filename}')
                    failed_count += 1
                    continue

                # Check for duplicate files
                file_hash = get_file_hash(file_path)
                app.logger.info(f'File uploaded: {original_filename} (hash: {file_hash[:8]}...)')

                # Create thumbnail for images only
                if get_file_type(filename) == 'image':
                    thumbnail_filename = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"
                    thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
                    if create_thumbnail(file_path, thumbnail_path):
                        app.logger.info(f'Thumbnail created for {original_filename}')
                    else:
                        app.logger.warning(f'Failed to create thumbnail for {original_filename}')

                uploaded_count += 1

            except Exception as e:
                app.logger.error(f'Error processing file {original_filename}: {str(e)}')
                if os.path.exists(file_path):
                    os.remove(file_path)
                flash(f'Error processing file: {original_filename}')
                failed_count += 1

    # Report results
    if uploaded_count > 0:
        app.logger.info(f'Successfully uploaded {uploaded_count} files from {get_real_client_ip()}')
        flash(f'Successfully uploaded {uploaded_count} file(s)!')

    if failed_count > 0:
        app.logger.warning(f'{failed_count} files failed to upload from {get_real_client_ip()}')
        flash(f'{failed_count} file(s) failed to upload due to validation errors.')

    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Sanitize filename to prevent directory traversal
    filename = secure_filename(filename)
    if not filename:
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/thumbnails/<filename>')
def thumbnail_file(filename):
    # Sanitize filename to prevent directory traversal
    filename = secure_filename(filename)
    if not filename:
        abort(404)
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)