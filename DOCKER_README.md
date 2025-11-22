# Wedding Uploader - Docker Setup

## Quick Start

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at `http://localhost:5000`

## Persistent Storage

### How It Works

This Docker setup uses **bind mounts** to ensure your uploaded files persist on the host machine. The following directories are mapped:

| Host Directory | Container Directory | Purpose |
|---------------|---------------------|---------|
| `./uploads` | `/app/uploads` | Stores original wedding photos and videos |
| `./thumbnails` | `/app/thumbnails` | Stores generated thumbnail images |

### What This Means

Your files are **always safe** and will persist through:

- ✅ Container stops (`docker-compose stop`)
- ✅ Container removal (`docker-compose down`)
- ✅ Container rebuilds (`docker-compose build`)
- ✅ Image updates (pulling new versions)
- ✅ System reboots
- ✅ Docker daemon restarts

### Verifying Persistence

You can verify that files persist by following these steps:

```bash
# 1. Start the container
docker-compose up -d

# 2. Upload a file through the web interface (http://localhost:5000)

# 3. Check that files appear on your host machine
ls -la uploads/
ls -la thumbnails/

# 4. Stop and remove the container
docker-compose down

# 5. Verify files still exist on host
ls -la uploads/
ls -la thumbnails/

# 6. Start the container again
docker-compose up -d

# 7. Visit http://localhost:5000 - your files should still be there!
```

### File Locations

Files are stored in your project directory:

```
C:\Users\Steven\Desktop\Projects\WeddingUploader\
├── uploads/          ← Wedding photos and videos
└── thumbnails/       ← Generated thumbnails
```

You can access these files directly from Windows Explorer at any time, even while the container is running.

## Backup and Restore

### Backup

To backup all uploaded files, simply copy the directories:

```bash
# Create a backup
mkdir -p backups/backup-$(date +%Y%m%d)
cp -r uploads/ backups/backup-$(date +%Y%m%d)/
cp -r thumbnails/ backups/backup-$(date +%Y%m%d)/
```

Or on Windows:
```cmd
mkdir backups\backup-%DATE%
xcopy uploads backups\backup-%DATE%\uploads /E /I
xcopy thumbnails backups\backup-%DATE%\thumbnails /E /I
```

### Restore

To restore from a backup:

```bash
# Stop the container
docker-compose down

# Restore files
cp -r backups/backup-20240115/uploads/* uploads/
cp -r backups/backup-20240115/thumbnails/* thumbnails/

# Start the container
docker-compose up -d
```

## Docker Commands

### Basic Operations

```bash
# Start in background
docker-compose up -d

# Start with logs visible
docker-compose up

# Stop container (keeps data)
docker-compose stop

# Start stopped container
docker-compose start

# Stop and remove container (data persists on host)
docker-compose down

# Rebuild and start
docker-compose up -d --build

# View logs
docker-compose logs -f wedding-uploader

# Check container status
docker-compose ps
```

### Updating the Application

When you update the application code:

```bash
# 1. Stop the container
docker-compose down

# 2. Rebuild with new code
docker-compose build

# 3. Start with new image
docker-compose up -d

# Your files in ./uploads and ./thumbnails remain intact!
```

### Clean Restart (Keep Files)

```bash
# Remove container and image, but keep files
docker-compose down
docker rmi wedding-uploader

# Rebuild and start fresh
docker-compose up -d --build

# Files are still there!
```

## Alternative: Named Volumes

If you prefer Docker-managed volumes instead of bind mounts, see `docker-compose.named-volumes.yml`:

```bash
docker-compose -f docker-compose.named-volumes.yml up -d
```

Named volumes are stored in Docker's internal storage and provide:
- Better performance on Windows/Mac
- More portable across systems
- Managed by Docker

However, files are not directly visible on the host filesystem.

## Changing Storage Location

To store files in a different location, edit `docker-compose.yml`:

```yaml
volumes:
  # Use absolute path for custom location
  - /path/to/your/storage/uploads:/app/uploads
  - /path/to/your/storage/thumbnails:/app/thumbnails
```

On Windows:
```yaml
volumes:
  - D:\wedding-storage\uploads:/app/uploads
  - D:\wedding-storage\thumbnails:/app/thumbnails
```

## Troubleshooting

### Files Not Persisting

If files disappear after restart:

1. Check that you're using `docker-compose down` and not `docker-compose down -v` (the `-v` flag removes volumes)
2. Verify the directories exist on the host: `ls uploads thumbnails`
3. Check volume mounts: `docker inspect wedding-uploader | grep Mounts -A 20`

### Permission Issues

If you get permission errors:

```bash
# On Linux/Mac, ensure directories have correct permissions
sudo chown -R $USER:$USER uploads thumbnails
chmod -R 755 uploads thumbnails
```

### Checking What's Mounted

To verify volumes are correctly mounted:

```bash
docker inspect wedding-uploader --format='{{json .Mounts}}' | python -m json.tool
```

You should see:
```json
[
    {
        "Type": "bind",
        "Source": "/path/to/your/project/uploads",
        "Destination": "/app/uploads",
        ...
    },
    {
        "Type": "bind",
        "Source": "/path/to/your/project/thumbnails",
        "Destination": "/app/thumbnails",
        ...
    }
]
```

## Storage Capacity Planning

- Each photo: 2-10 MB (typical)
- Each video: 50-500 MB (typical)
- Thumbnails: ~50-100 KB each

Example storage requirements:
- 100 photos: ~500 MB
- 20 videos: ~2-5 GB
- Thumbnails: ~10 MB

**Recommendation:** Ensure at least 10-20 GB of free space for a typical wedding.

## Data Migration

### Moving to a New Server

```bash
# On old server
docker-compose down
tar -czf wedding-backup.tar.gz uploads/ thumbnails/

# Transfer wedding-backup.tar.gz to new server

# On new server
tar -xzf wedding-backup.tar.gz
docker-compose up -d
```

### Cloud Storage Backup

Consider setting up automated backups to cloud storage:

```bash
# Example: Sync to cloud (add to cron)
rclone sync uploads/ remote:wedding-uploads/
rclone sync thumbnails/ remote:wedding-thumbnails/
```

## Security Notes

- Files are stored with the same permissions as the user running Docker
- On Linux, files are owned by the user inside the container (usually root)
- Use `chown` to adjust ownership if needed
- Consider encrypting backups if storing sensitive wedding photos

## Support

For issues specific to Docker setup, check:
- Docker logs: `docker-compose logs -f`
- Container status: `docker-compose ps`
- Volume inspection: `docker inspect wedding-uploader`

For application issues, check the main README or application logs.
