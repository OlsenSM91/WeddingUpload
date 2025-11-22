# Wedding Gallery Uploader

<img width="1261" height="1268" alt="Screenshot 2025-11-22 075042" src="https://github.com/user-attachments/assets/3b1d6b9b-307e-491d-84df-b248db140298" />

A beautiful, secure, and easy-to-deploy web application for collecting and sharing wedding photos and videos. Perfect for allowing wedding guests to upload and view memories from your special day in a centralized gallery.

## Features

### Core Functionality
- **Multi-file Upload** - Upload multiple photos and videos simultaneously (up to 10 files per request)
- **Drag & Drop Interface** - Intuitive drag-and-drop upload area with progress tracking
- **Image Gallery** - Responsive grid layout displaying all uploaded media
- **Video Support** - Supports MP4, MOV, AVI, MKV, and WebM video formats
- **Automatic Thumbnails** - Generates optimized 300x300px thumbnails for images
- **Fullscreen Preview** - Click on any image to view it fullscreen
- **Duplicate Detection** - Prevents uploading duplicate files (MD5 hash-based)
- **Upload Progress Tracking** - Real-time progress bar showing upload status

### Security Features
- **File Validation** - Multi-layer validation using file extensions, MIME types, and content verification
- **Secure Filenames** - Automatic filename sanitization to prevent directory traversal attacks
- **Size Limits** - 50MB per file, 10 files maximum per upload
- **Security Headers** - X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP
- **Image Integrity Checks** - PIL-based verification to ensure uploaded images are valid
- **Request Logging** - Comprehensive logging with real client IP detection (CloudFlare support)
- **IPv6 Support** - Smart IP detection with IPv4 preference and IPv6 compression

### User Experience
- **Beautiful UI** - Modern gradient design with smooth animations
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile devices
- **File Management** - Add, remove, or clear selected files before uploading
- **Upload Timestamps** - Displays when each file was uploaded
- **Flash Messages** - User-friendly success/error notifications
- **No Registration Required** - Open for all guests to share memories

## Requirements

### For Docker Deployment (Recommended)
- Docker (20.10+)
- Docker Compose (2.0+)

### For Manual Deployment
- Python 3.8+
- pip (Python package manager)
- **Linux/Mac:** libmagic library (`apt-get install libmagic1` on Debian/Ubuntu, `brew install libmagic` on Mac)
- **Windows:** No additional system libraries needed (python-magic-bin includes binaries)

### Dependencies Files

The project includes two requirements files:

- **`requirements.txt`** - For Docker/Linux/Mac deployment (uses `python-magic`)
- **`requirements-windows.txt`** - For Windows local development (uses `python-magic-bin`)

> **Why two files?** The `python-magic` library requires the system `libmagic` library. On Linux/Docker, we install `libmagic1` via apt. On Windows, `python-magic-bin` includes the Windows DLL files, so no separate installation is needed.

## Quick Start with Docker

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/OlsenSM91/WeddingUpload.git
cd wedding-uploader

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f
```

The application will be available at `http://localhost:5000`

## Docker Deployment (Detailed)

### Understanding Persistent Storage

This application uses **Docker bind mounts** to ensure your uploaded wedding photos and videos are permanently stored on your host machine, not inside the container. This means your files are safe even if you:

- Stop the container
- Remove the container
- Rebuild the image
- Update the application
- Restart your server

### How Storage Works

The `docker-compose.yml` file contains these volume mappings:

```yaml
volumes:
  - ./uploads:/app/uploads          # Wedding photos and videos
  - ./thumbnails:/app/thumbnails    # Generated thumbnails
```

This configuration creates two folders in your project directory:

```
wedding-uploader/
├── uploads/          ← All uploaded photos and videos stored here
├── thumbnails/       ← Auto-generated thumbnails stored here
├── app.py
├── docker-compose.yml
└── ...
```

**Important:** These folders exist on your **host machine** (your server), not inside Docker. You can:
- Access them directly through your file explorer
- Back them up by copying the folders
- Move them to external storage
- Browse files even when Docker is stopped

### Storage Locations

| What | Where on Host | Where in Container | Purpose |
|------|--------------|-------------------|---------|
| Original files | `./uploads/` | `/app/uploads/` | Wedding photos and videos |
| Thumbnails | `./thumbnails/` | `/app/thumbnails/` | Optimized preview images |

### Docker Commands

#### Starting the Application

```bash
# Start in background (detached mode)
docker-compose up -d

# Start with logs visible
docker-compose up

# Start and rebuild if code changed
docker-compose up -d --build
```

#### Monitoring

```bash
# View real-time logs
docker-compose logs -f

# Check container status
docker-compose ps

# Check resource usage
docker stats wedding-uploader
```

#### Stopping

```bash
# Stop container (data persists on host)
docker-compose stop

# Stop and remove container (data still persists on host!)
docker-compose down

# DANGEROUS: Remove container AND volumes (deletes all uploads!)
docker-compose down -v   # ⚠️ NEVER use -v flag unless you want to delete files!
```

#### Updating the Application

When updating to a new version:

```bash
# Pull latest code
git pull origin main

# Stop current container
docker-compose down

# Rebuild with new code
docker-compose build

# Start with new version
docker-compose up -d

# Your files in ./uploads and ./thumbnails remain intact!
```

### Changing the Port

To run on a different port, edit `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Access at http://localhost:8080
```

### Custom Storage Location

To store files in a different location (e.g., external drive), edit `docker-compose.yml`:

```yaml
volumes:
  # Use absolute paths for custom locations
  - /mnt/external-drive/wedding-uploads:/app/uploads
  - /mnt/external-drive/wedding-thumbnails:/app/thumbnails
```

On Windows:
```yaml
volumes:
  - D:\WeddingStorage\uploads:/app/uploads
  - D:\WeddingStorage\thumbnails:/app/thumbnails
```

### Environment Variables

You can customize the application using environment variables. Create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your settings
```

Then update `docker-compose.yml` to use it:

```yaml
services:
  wedding-uploader:
    env_file:
      - .env
```

Available variables:
- `FLASK_SECRET_KEY` - Secret key for session management (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `FLASK_ENV` - Set to `production` for production deployments
- `FLASK_DEBUG` - Set to `False` for production
- `MAX_CONTENT_LENGTH` - Maximum file size in bytes (default: 52428800 = 50MB)

## Manual Installation (Without Docker)

If you prefer to run without Docker:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/wedding-uploader.git
cd wedding-uploader
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

**For Linux/Mac:**
```bash
pip install -r requirements.txt
```

**For Windows:**
```bash
pip install -r requirements-windows.txt
```

> **Note:** Windows uses `python-magic-bin` (includes Windows binaries), while Linux/Mac uses `python-magic` (requires system `libmagic` library). Docker always uses the Linux requirements.

### 4. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 5. For Production

For production deployments, use a production WSGI server:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Configuration

### File Restrictions

Configure these settings in `app.py`:

```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mkv', 'webm'}
MAX_FILES_PER_REQUEST = 10
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
THUMBNAIL_SIZE = (300, 300)
```

### Security Settings

The application includes several security features enabled by default:

- **Secret Key**: Change the default secret key in `app.py` line 16 (or use environment variable)
- **Max Upload Size**: 50MB per file (configurable)
- **Content Security Policy**: Restricts external resource loading
- **XSS Protection**: Enabled via security headers
- **Frame Protection**: Prevents clickjacking attacks

## Usage

### For Wedding Guests

1. Navigate to the wedding gallery URL
2. Click "Choose Files" or drag files into the upload area
3. Select multiple photos/videos (up to 10 files at once)
4. Review selected files and click "Upload Selected Files"
5. Wait for upload to complete
6. Browse the gallery to view all shared memories

### For Administrators

#### Viewing Logs

Docker:
```bash
docker-compose logs -f wedding-uploader
```

Manual:
```bash
# Logs are printed to console by default
# For file logging, redirect output:
python app.py > app.log 2>&1
```

#### Accessing Uploaded Files

Files are stored in:
- `uploads/` - Original files with UUID prefixes (e.g., `abc123_photo.jpg`)
- `thumbnails/` - Thumbnails prefixed with `thumb_` (e.g., `thumb_abc123.jpg`)

#### Monitoring Storage

```bash
# Check storage usage (Linux/Mac)
du -sh uploads/ thumbnails/

# Check storage usage (Windows)
dir uploads /s
dir thumbnails /s

# Count files
ls -1 uploads/ | wc -l     # Linux/Mac
dir /b uploads | find /c /v ""   # Windows
```

## Backup and Restore

### Backup Strategy

Since files are stored on the host filesystem, backups are simple:

#### Quick Backup (Manual)

```bash
# Create backup directory with timestamp
mkdir -p backups/backup-$(date +%Y%m%d-%H%M%S)

# Copy files
cp -r uploads/ backups/backup-$(date +%Y%m%d-%H%M%S)/
cp -r thumbnails/ backups/backup-$(date +%Y%m%d-%H%M%S)/
```

Windows:
```cmd
mkdir backups\backup-%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%
xcopy uploads backups\backup-%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%\uploads /E /I
xcopy thumbnails backups\backup-%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%\thumbnails /E /I
```

#### Automated Backup (Recommended)

Create a backup script `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups/wedding-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/wedding-files.tar.gz" uploads/ thumbnails/
echo "Backup completed: $BACKUP_DIR"
```

Add to crontab for daily backups:
```bash
0 2 * * * /path/to/backup.sh
```

#### Cloud Backup

Using rclone to backup to cloud storage:

```bash
# Install rclone and configure your cloud provider
rclone sync uploads/ remote:wedding-uploads/
rclone sync thumbnails/ remote:wedding-thumbnails/
```

### Restore from Backup

```bash
# Stop the application
docker-compose down

# Restore files
cp -r backups/backup-20240115/uploads/* uploads/
cp -r backups/backup-20240115/thumbnails/* thumbnails/

# Start the application
docker-compose up -d
```

## Storage Capacity Planning

### Typical File Sizes
- **Photos (JPEG)**: 2-10 MB each
- **Photos (PNG)**: 5-15 MB each
- **Videos (MP4, 1080p)**: 50-200 MB per minute
- **Videos (4K)**: 200-500 MB per minute
- **Thumbnails**: 50-100 KB each

### Example Storage Requirements

| Scenario | Photos | Videos | Total Storage |
|----------|--------|--------|---------------|
| Small wedding | 100 photos | 5 videos (5 min) | ~2-3 GB |
| Medium wedding | 300 photos | 15 videos (10 min) | ~5-8 GB |
| Large wedding | 500 photos | 30 videos (15 min) | ~10-15 GB |

**Recommendation:** Allocate at least **20-30 GB** of free space for a typical wedding.

## Security Considerations

### Production Deployment Checklist

Before deploying to production:

- [ ] Change the secret key in `app.py` or set `FLASK_SECRET_KEY` environment variable
- [ ] Set `debug=False` in `app.py` line 372
- [ ] Use a production WSGI server (Gunicorn, uWSGI) instead of Flask's development server
- [ ] Enable HTTPS using a reverse proxy (Nginx, Caddy, Traefik)
- [ ] Set up regular automated backups
- [ ] Configure firewall rules to restrict access
- [ ] Monitor disk space and set up alerts
- [ ] Review and adjust file size limits based on your needs
- [ ] Consider adding authentication if gallery should be private

### Reverse Proxy Setup (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name wedding.yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

For HTTPS (recommended):

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d wedding.yourdomain.com
```

### CloudFlare Integration

The application automatically detects real client IPs when behind CloudFlare using:
- `CF-Connecting-IP` header
- `CF-Connecting-IPv6` header
- `CF-Pseudo-IPv4` header

This ensures accurate logging and rate limiting even when proxied through CloudFlare.

## Development

### Project Structure

```
wedding-uploader/
├── app.py                          # Flask application (main backend)
├── templates/
│   └── index.html                  # Frontend template
├── uploads/                        # User-uploaded files (git-ignored)
├── thumbnails/                     # Generated thumbnails (git-ignored)
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker image configuration
├── docker-compose.yml              # Docker orchestration
├── .dockerignore                   # Docker build exclusions
├── .env.example                    # Environment variable template
├── DOCKER_README.md               # Docker-specific documentation
└── README.md                       # This file
```

### Key Dependencies

- **Flask 2.3.3** - Web framework
- **Werkzeug 2.3.7** - WSGI utilities (secure_filename, file handling)
- **Pillow 10.0.1** - Image processing and thumbnail generation
- **python-magic 0.4.27** - MIME type detection (Linux/Mac/Docker)
- **python-magic-bin 0.4.14** - MIME type detection (Windows only)

### Making Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test locally: `python app.py`
5. Test with Docker: `docker-compose up --build`
6. Commit changes: `git commit -am "Add feature"`
7. Push to branch: `git push origin feature-name`
8. Create Pull Request

### Adding Features

Some ideas for future enhancements:
- User authentication / password protection
- Download all files as ZIP
- Admin panel for managing uploads
- Comments on photos
- EXIF data display
- Photo tagging and search
- Integration with cloud storage (S3, Google Drive)
- Email notifications on new uploads

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs wedding-uploader

# Check if port 5000 is in use
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Remove old containers
docker-compose down
docker-compose up -d
```

### Files Not Persisting

```bash
# Verify volume mounts
docker inspect wedding-uploader | grep -A 10 Mounts

# Check that you're not using -v flag
docker-compose down  # ✅ Correct
docker-compose down -v  # ❌ Wrong - deletes volumes!
```

### Upload Fails

Common causes:
- File too large (>50MB)
- Invalid file type
- Insufficient disk space
- File corruption

Check logs:
```bash
docker-compose logs -f wedding-uploader
```

### Permission Issues (Linux)

```bash
# Fix ownership
sudo chown -R $USER:$USER uploads/ thumbnails/

# Fix permissions
chmod -R 755 uploads/ thumbnails/
```

### Out of Disk Space

```bash
# Check available space
df -h

# Find large files
du -sh uploads/* | sort -h

# Clean Docker system (careful!)
docker system prune -a
```

### Thumbnail Generation Fails

Usually caused by:
- Corrupted image files
- Unsupported image formats
- Insufficient memory

Check logs for specific errors:
```bash
docker-compose logs -f | grep -i thumbnail
```

## Performance Optimization

### For High Traffic

1. **Use Gunicorn with multiple workers:**
   ```yaml
   command: gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Add Nginx as reverse proxy** for static file serving

3. **Use CDN** for thumbnails and uploaded images

4. **Enable gzip compression** in reverse proxy

5. **Add Redis** for session storage (if adding authentication)

### Storage Optimization

1. **Compress images** on upload (add to `create_thumbnail` function)
2. **Use object storage** (S3, MinIO) for uploaded files
3. **Implement file retention policy** (auto-delete after X days)
4. **Convert videos** to web-optimized formats

## FAQ

### Can guests delete photos they uploaded?

Not by default. To add this feature, you would need to implement authentication and track which user uploaded which file.

### Can I password protect the gallery?

Yes, you can add Flask-Login or Flask-HTTPAuth for basic authentication. This would require modifying `app.py`.

### Can I change the maximum file size?

Yes, edit `app.py` line 17:
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

And line 156:
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

### Can I deploy this on a Raspberry Pi?

Yes! Use the ARM-compatible Docker image or run manually with Python. Note: Video processing may be slower on Raspberry Pi.

### How do I migrate to a new server?

1. Stop the application: `docker-compose down`
2. Copy the entire project directory to the new server
3. Start on new server: `docker-compose up -d`

All files are in `uploads/` and `thumbnails/`, which move with your project.

### Can I use this for non-wedding events?

Absolutely! Just edit the titles and text in `templates/index.html` to customize for any event (birthday, conference, reunion, etc.).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under The Unlicense License. You are free to use, destribute, sell or otherwise do whatever you would like with this code and the creator can not be held liable for anything.

## Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search [existing issues](https://github.com/yourusername/wedding-uploader/issues)
3. Create a [new issue](https://github.com/yourusername/wedding-uploader/issues/new) with:
   - Description of the problem
   - Steps to reproduce
   - Your environment (OS, Docker version, etc.)
   - Relevant log output

## Acknowledgments

Built with:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Pillow](https://python-pillow.org/) - Image processing
- [python-magic](https://github.com/ahupp/python-magic) - MIME type detection
- [Docker](https://www.docker.com/) - Containerization

---

**Made with ❤️ by Steven Olsen**
