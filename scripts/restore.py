#!/usr/bin/env python3
"""
Industrace Restore Script
Restores a complete backup of the Industrace system including:
- Database restore
- Uploaded files restore
- Configuration files restore
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import tarfile
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IndustraceRestore:
    def __init__(self, backup_file, restore_dir="restore_temp"):
        self.backup_file = Path(backup_file)
        self.restore_dir = Path(restore_dir)
        self.extracted_dir = None
        
        if not self.backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
    
    def restore(self, force=False):
        """Restore Industrace from backup"""
        logger.info(f"Starting Industrace restore from: {self.backup_file}")
        
        try:
            # 1. Extract backup
            self.extract_backup()
            
            # 2. Validate backup
            self.validate_backup()
            
            # 3. Stop services (if running)
            if not force:
                self.stop_services()
            
            # 4. Restore database
            self.restore_database()
            
            # 5. Restore uploads
            self.restore_uploads()
            
            # 6. Restore configuration (optional)
            self.restore_config()
            
            # 7. Cleanup
            self.cleanup()
            
            logger.info("Restore completed successfully")
            print("✅ Restore completed successfully!")
            print("🚀 You can now start Industrace with: make prod")
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            self.cleanup()
            raise
    
    def extract_backup(self):
        """Extract backup archive"""
        logger.info("Extracting backup...")
        
        # Create restore directory
        self.restore_dir.mkdir(exist_ok=True)
        
        # Extract archive
        with tarfile.open(self.backup_file, "r:gz") as tar:
            tar.extractall(self.restore_dir)
        
        # Find extracted directory
        extracted_dirs = list(self.restore_dir.glob("industrace_backup_*"))
        if not extracted_dirs:
            raise Exception("No backup directory found in archive")
        
        self.extracted_dir = extracted_dirs[0]
        logger.info(f"Backup extracted to: {self.extracted_dir}")
    
    def validate_backup(self):
        """Validate backup contents"""
        logger.info("Validating backup...")
        
        required_files = [
            "metadata.json",
            "database.sql"
        ]
        
        for file_name in required_files:
            file_path = self.extracted_dir / file_name
            if not file_path.exists():
                raise Exception(f"Required backup file missing: {file_name}")
        
        # Read metadata
        metadata_file = self.extracted_dir / "metadata.json"
        with open(metadata_file, 'r') as f:
            self.metadata = json.load(f)
        
        logger.info(f"Backup validation passed. Created: {self.metadata.get('created_at')}")
    
    def stop_services(self):
        """Stop running services"""
        logger.info("Stopping services...")
        
        try:
            # Try different docker-compose files
            compose_files = ["docker-compose.prod.yml", "docker-compose.yml", "docker-compose.dev.yml"]
            stopped = False
            
            for compose_file in compose_files:
                if not Path(compose_file).exists():
                    continue
                    
                # Check if docker-compose is running
                result = subprocess.run(
                    ["docker-compose", "-f", compose_file, "ps", "-q"], 
                    capture_output=True, 
                    text=True
                )
                
                if result.stdout.strip():
                    logger.info(f"Stopping docker-compose services ({compose_file})...")
                    subprocess.run(["docker-compose", "-f", compose_file, "down"], check=True)
                    logger.info("Services stopped")
                    stopped = True
                    break
            
            if not stopped:
                logger.info("No running services found")
                
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not stop services: {e}")
        except FileNotFoundError:
            logger.warning("docker-compose not found, skipping service stop")
    
    def restore_database(self):
        """Restore PostgreSQL database using docker-compose exec"""
        logger.info("Restoring database...")
        
        try:
            # Try to use docker-compose exec first (if containers are running)
            compose_file = None
            for compose_file_option in ["docker-compose.prod.yml", "docker-compose.yml", "docker-compose.dev.yml"]:
                if Path(compose_file_option).exists():
                    compose_file = compose_file_option
                    break
            
            # Database dump file
            dump_file = self.extracted_dir / "database.sql"
            
            if compose_file:
                # Check if database container is running
                result = subprocess.run(
                    ["docker-compose", "-f", compose_file, "ps", "-q", "db"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Use docker-compose exec to restore from container
                    logger.info(f"Using docker-compose exec with {compose_file}")
                    
                    # Drop and recreate database
                    logger.info("Dropping existing database...")
                    drop_cmd = [
                        "docker-compose", "-f", compose_file, "exec", "-T", "db",
                        "psql", "-U", "industrace_user", "-d", "postgres",
                        "-c", "DROP DATABASE IF EXISTS industrace;"
                    ]
                    subprocess.run(drop_cmd, check=True)
                    
                    logger.info("Creating new database...")
                    create_cmd = [
                        "docker-compose", "-f", compose_file, "exec", "-T", "db",
                        "psql", "-U", "industrace_user", "-d", "postgres",
                        "-c", "CREATE DATABASE industrace;"
                    ]
                    subprocess.run(create_cmd, check=True)
                    
                    logger.info("Restoring database from dump...")
                    with open(dump_file, 'r') as f:
                        restore_cmd = [
                            "docker-compose", "-f", compose_file, "exec", "-T", "db",
                            "psql", "-U", "industrace_user", "-d", "industrace"
                        ]
                        subprocess.run(restore_cmd, stdin=f, check=True)
                    
                    logger.info("Database restore completed")
                    return
            
            # Fallback: direct connection (if containers are not running)
            logger.info("Containers not running, trying direct connection...")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "industrace")
            db_user = os.getenv("DB_USER", "industrace_user")
            db_password = os.getenv("DB_PASSWORD")
            
            if not db_password:
                raise Exception("DB_PASSWORD environment variable is required when containers are not running")
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password
            
            # Drop and recreate database
            drop_cmd = [
                "psql",
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", "postgres",
                "--no-password",
                "-c", f"DROP DATABASE IF EXISTS {db_name};"
            ]
            
            create_cmd = [
                "psql",
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", "postgres",
                "--no-password",
                "-c", f"CREATE DATABASE {db_name};"
            ]
            
            # Restore database
            restore_cmd = [
                "psql",
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", db_name,
                "--no-password",
                "-f", str(dump_file)
            ]
            
            # Execute commands
            logger.info("Dropping existing database...")
            subprocess.run(drop_cmd, env=env, check=True)
            
            logger.info("Creating new database...")
            subprocess.run(create_cmd, env=env, check=True)
            
            logger.info("Restoring database from dump...")
            subprocess.run(restore_cmd, env=env, check=True)
            
            logger.info("Database restore completed")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Database restore failed: {e}")
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            raise
    
    def restore_uploads(self):
        """Restore uploaded files"""
        logger.info("Restoring uploads...")
        
        backup_uploads_dir = self.extracted_dir / "uploads"
        if backup_uploads_dir.exists():
            # Remove existing uploads
            uploads_dir = Path("uploads")
            if uploads_dir.exists():
                shutil.rmtree(uploads_dir)
            
            # Restore uploads
            shutil.copytree(backup_uploads_dir, uploads_dir)
            logger.info("Uploads restore completed")
        else:
            logger.warning("No uploads found in backup, skipping")
    
    def restore_config(self):
        """Restore configuration files (optional)"""
        logger.info("Restoring configuration...")
        
        backup_config_dir = self.extracted_dir / "config"
        if backup_config_dir.exists():
            # List config files
            config_files = list(backup_config_dir.glob("*"))
            
            if config_files:
                print("Configuration files found in backup:")
                for config_file in config_files:
                    print(f"  - {config_file.name}")
                
                response = input("Do you want to restore configuration files? (y/N): ")
                if response.lower() in ['y', 'yes']:
                    for config_file in config_files:
                        target_file = Path(config_file.name)
                        if target_file.exists():
                            backup_file = target_file.with_suffix(f"{target_file.suffix}.backup")
                            shutil.move(target_file, backup_file)
                            logger.info(f"Backed up existing: {target_file} -> {backup_file}")
                        
                        shutil.copy2(config_file, target_file)
                        logger.info(f"Restored: {config_file.name}")
                else:
                    logger.info("Configuration restore skipped")
            else:
                logger.info("No configuration files found in backup")
        else:
            logger.info("No configuration backup found, skipping")
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.restore_dir.exists():
            shutil.rmtree(self.restore_dir)
            logger.info("Temporary files cleaned up")

def main():
    parser = argparse.ArgumentParser(description="Industrace Restore Script")
    parser.add_argument(
        "backup_file", 
        help="Backup file to restore from"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force restore without stopping services"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List available backups"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
        return
    
    try:
        restore = IndustraceRestore(args.backup_file)
        restore.restore(force=args.force)
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        sys.exit(1)

def list_backups():
    """List available backups"""
    backup_path = Path("backups")
    
    if not backup_path.exists():
        print("No backup directory found")
        return
    
    backups = []
    for file_path in backup_path.glob("industrace_backup_*.tar.gz"):
        stat = file_path.stat()
        backups.append({
            "name": file_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime)
        })
    
    if not backups:
        print("No backups found")
        return
    
    print(f"Available backups:")
    print("-" * 80)
    
    for i, backup in enumerate(sorted(backups, key=lambda x: x["modified"], reverse=True)):
        size_mb = backup["size"] / (1024 * 1024)
        print(f"{i+1:2d}. {backup['name']:<50} {size_mb:>8.2f} MB  {backup['modified'].strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 