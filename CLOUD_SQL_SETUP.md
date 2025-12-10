# Cloud SQL Setup Guide

This guide walks you through setting up Google Cloud SQL for the Actions Service microservice.

## Prerequisites

- Google Cloud Platform (GCP) account
- `gcloud` CLI installed and authenticated
- Project ID where you want to create the Cloud SQL instance

## Step 1: Create Cloud SQL Instance

### Option A: Using gcloud CLI

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Create a MySQL 8.0 instance
gcloud sql instances create unified-inbox-db \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YOUR_ROOT_PASSWORD \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00 \
  --enable-bin-log

# Note: Replace YOUR_ROOT_PASSWORD with a strong password
# Note: db-f1-micro is the smallest tier (suitable for development)
#       For production, consider db-n1-standard-1 or higher
```

### Option B: Using Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **SQL** in the left menu
3. Click **Create Instance**
4. Choose **MySQL**
5. Fill in:
   - **Instance ID**: `unified-inbox-db`
   - **Root password**: Set a strong password (save this!)
   - **Region**: Choose closest to you (e.g., `us-central1`)
   - **Database version**: MySQL 8.0
   - **Machine type**: `db-f1-micro` (for dev) or higher for production
   - **Storage**: 10GB SSD (minimum)
6. Click **Create**

## Step 2: Create Database

```bash
# Create the database
gcloud sql databases create unified_inbox \
  --instance=unified-inbox-db
```

Or via Console:
1. Go to your SQL instance
2. Click **Databases** tab
3. Click **Create database**
4. Name: `unified_inbox`
5. Click **Create**

## Step 3: Create Application User (Recommended)

For security, create a dedicated user instead of using root:

```bash
# Create a user
gcloud sql users create app_user \
  --instance=unified-inbox-db \
  --password=YOUR_APP_PASSWORD

# Grant privileges (connect to instance first)
# You'll need to connect and run SQL:
```

Or via Console:
1. Go to your SQL instance
2. Click **Users** tab
3. Click **Add user account**
4. Username: `app_user`
5. Password: Set a strong password
6. Click **Add**

Then grant privileges by connecting to the database and running:
```sql
GRANT ALL PRIVILEGES ON unified_inbox.* TO 'app_user'@'%';
FLUSH PRIVILEGES;
```

## Step 4: Get Connection Information

```bash
# Get connection name (needed for Cloud Run)
gcloud sql instances describe unified-inbox-db \
  --format="value(connectionName)"

# Output will be: PROJECT_ID:REGION:INSTANCE_NAME
# Example: my-project:us-central1:unified-inbox-db

# Get public IP (if using TCP connection)
gcloud sql instances describe unified-inbox-db \
  --format="value(ipAddresses[0].ipAddress)"
```

## Step 5: Run Database Migrations

You have two options to run the migrations:

### Option A: Using Cloud SQL Proxy (Recommended for local development)

1. **Install Cloud SQL Proxy**:
   ```bash
   # Download Cloud SQL Proxy
   curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.arm64
   chmod +x cloud-sql-proxy
   
   # Or for Linux:
   # curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
   ```

2. **Start the proxy** (in a separate terminal):
   ```bash
   ./cloud-sql-proxy PROJECT_ID:REGION:INSTANCE_NAME
   # Example: ./cloud-sql-proxy my-project:us-central1:unified-inbox-db
   ```
   This will create a local socket at `127.0.0.1:3306`

3. **Connect and run migrations**:
   ```bash
   # Connect to the database through the proxy
   mysql -h 127.0.0.1 -u app_user -p unified_inbox
   
   # Or using the root user:
   # mysql -h 127.0.0.1 -u root -p unified_inbox
   
   # Then run the migrations:
   source migrations/create_todos_table.sql
   source migrations/create_followups_table.sql
   ```

### Option B: Using gcloud sql connect

```bash
# Connect directly (requires authorized networks or Cloud Shell)
gcloud sql connect unified-inbox-db --user=root

# Once connected, run:
USE unified_inbox;
SOURCE migrations/create_todos_table.sql;
SOURCE migrations/create_followups_table.sql;
```

### Option C: Using MySQL Workbench or other GUI

1. Get the public IP from Step 4
2. Add your local IP to authorized networks (see Step 6)
3. Connect using:
   - Host: `<public-ip>`
   - Port: `3306`
   - Username: `app_user` or `root`
   - Password: Your password
   - Database: `unified_inbox`
4. Run the SQL files from `migrations/` directory

## Step 6: Configure Authorized Networks (for TCP access)

If you want to connect from your local machine via TCP:

```bash
# Get your public IP
curl ifconfig.me

# Add authorized network
gcloud sql instances patch unified-inbox-db \
  --authorized-networks=YOUR_PUBLIC_IP/32
```

Or via Console:
1. Go to your SQL instance
2. Click **Connections**
3. Under **Authorized networks**, click **Add network**
4. Enter your public IP with `/32` (e.g., `123.45.67.89/32`)
5. Click **Done** and **Save**

**Note**: For Cloud Run, you don't need authorized networks - it uses Unix sockets automatically.

## Step 7: Configure Environment Variables

### For Local Development (using Cloud SQL Proxy)

Create/update your `.env` file:

```bash
# Using Cloud SQL Proxy (recommended for local dev)
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=unified_inbox
DB_USER=app_user
DB_PASSWORD=your_app_password

# Service URLs
INTEGRATIONS_SERVICE_URL=https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app
```

### For Cloud Run Deployment

You'll set these as environment variables in Cloud Run:
- `CLOUD_SQL_CONNECTION_NAME`: `PROJECT_ID:REGION:INSTANCE_NAME`
- `DB_UNIX_SOCKET`: `/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME`
- `DB_NAME`: `unified_inbox`
- `DB_USER`: `app_user`
- `DB_PASSWORD`: Your app password
- `INTEGRATIONS_SERVICE_URL`: `https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app`

## Step 8: Verify Connection

Test the connection locally:

```bash
# Make sure Cloud SQL Proxy is running (if using proxy)
# Then test with Python:
python3 -c "
from services.database import DatabaseManager
db = DatabaseManager()
if db.connection:
    print('✅ Successfully connected to Cloud SQL!')
    db.close()
else:
    print('❌ Connection failed')
"
```

## Troubleshooting

### Connection Refused
- Make sure Cloud SQL Proxy is running (if using proxy)
- Check authorized networks if using TCP
- Verify firewall rules

### Authentication Failed
- Double-check username and password
- Ensure user has proper privileges
- Try connecting with root user first

### Can't Find Socket
- Verify `CLOUD_SQL_CONNECTION_NAME` format: `PROJECT:REGION:INSTANCE`
- Check that Cloud SQL Proxy is running
- For Cloud Run, ensure Cloud SQL connection is enabled in service settings

## Next Steps

Once Cloud SQL is set up and migrations are run:
1. ✅ Phase 1 Complete - Database Setup
2. Proceed to Phase 2 - Data Models
3. Continue with remaining phases
