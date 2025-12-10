# Environment Configuration

This document describes the required environment variables for the Actions Service.

## Database Configuration

### Local MySQL Development
```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=unified_inbox
DB_USER=root
DB_PASSWORD=your_password
```

### Cloud SQL via Unix Socket (when running on GCP/Cloud Run)
```bash
CLOUD_SQL_CONNECTION_NAME=project:region:instance-name
DB_UNIX_SOCKET=/cloudsql/project:region:instance-name
DB_NAME=unified_inbox
DB_USER=your-cloud-sql-user
DB_PASSWORD=your-cloud-sql-password
```

### Cloud SQL via TCP (when running locally connecting to Cloud SQL)
```bash
DB_HOST=127.0.0.1  # or Cloud SQL public IP
DB_PORT=3306
DB_NAME=unified_inbox
DB_USER=your-cloud-sql-user
DB_PASSWORD=your-cloud-sql-password
```

## Service URLs

### Integrations Service
```bash
INTEGRATIONS_SERVICE_URL=https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app
```

### Classification Service (optional, for webhook/polling)
```bash
CLASSIFICATION_SERVICE_URL=
```

## Notes

- The service will automatically detect Cloud SQL connection if `CLOUD_SQL_CONNECTION_NAME` and `DB_UNIX_SOCKET` are set
- Otherwise, it will use standard TCP connection with `DB_HOST` and `DB_PORT`
- Default values are provided for local development
