# Backup Service (Restic)

This project uses a dedicated Docker service for secure, encrypted backups with [restic](https://restic.net/).

## Features
- Encrypted backups (restic)
- Remote repository support (SFTP, S3, B2, etc.)
- Retention policy (daily, weekly, monthly)
- Integrity check after backup
- Docker secrets for password
- Reusable pattern for other projects

## Usage

### 1. Configure secrets
Create a file `.env_prod_secrets/RESTIC_PASSWORD.txt` with your strong backup password (do not commit this file), add repository URL and hostname in `docker-compose.prod.yml` env vars:

```
RESTIC_REPOSITORY=sftp:user@backup-server:/path/to/repo
RESTIC_HOSTNAME=webshop-prod
```

### 2. Add secret to compose
In `docker-compose.prod.yml`:

```
secrets:
  RESTIC_PASSWORD:
    file: .env_prod_secrets/RESTIC_PASSWORD.txt
```

### 3. Run backup
Build and run with backup profile:

```
sudo docker compose -f docker-compose.prod.yml --profile backup up backup
```

### 4. Restore example
To restore:

```
sudo docker compose -f docker-compose.prod.yml run --rm backup restic restore latest --target /restore
```

## Customization
- Change `BACKUP_SRC` to the folder you want to backup (e.g. `/app/instance` for database volume)
- Adjust retention policy in compose env vars
- Use any remote supported by restic (SFTP, S3, B2, etc.)

## Security
- Password is stored as a Docker secret
- Repository is encrypted
- Only backup service mounts data as read-only

## Reusability
- Copy `backup/entrypoint.sh` and this compose service to any project
- Adjust `BACKUP_SRC`, secrets, and repository URL

## References
- [Restic Documentation](https://restic.readthedocs.io/en/latest/)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
