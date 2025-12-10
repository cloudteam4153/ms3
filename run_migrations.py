#!/usr/bin/env python3
"""
Script to run database migrations for todos and followups tables.
Make sure Cloud SQL Proxy is running before executing this script.
"""

import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()


def read_sql_file(filepath):
    """Read SQL file and return its contents"""
    with open(filepath, 'r') as f:
        return f.read()


def run_migration(connection, sql_file):
    """Execute a SQL migration file"""
    try:
        sql_content = read_sql_file(sql_file)
        cursor = connection.cursor()
        
        # Execute each statement (split by semicolon)
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                cursor.execute(statement)
        
        connection.commit()
        cursor.close()
        print(f"✅ Successfully ran migration: {sql_file}")
        return True
    except Error as e:
        print(f"❌ Error running migration {sql_file}: {e}")
        return False


def main():
    """Main function to run all migrations"""
    # Connect to database
    try:
        # Check if using Cloud SQL Proxy (local) or direct connection
        # Cloud SQL Proxy listens on 127.0.0.1, not localhost
        db_host = os.getenv('DB_HOST', '127.0.0.1')
        if db_host == 'localhost':
            db_host = '127.0.0.1'  # Force 127.0.0.1 for Cloud SQL Proxy
        db_port = int(os.getenv('DB_PORT', 3306))
        db_name = os.getenv('DB_NAME', 'unified_inbox')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')
        
        print(f"Connecting to database at {db_host}:{db_port}...")
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        if connection.is_connected():
            print(f"✅ Connected to database: {db_name}")
            
            # Get migration files
            migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
            todos_migration = os.path.join(migrations_dir, 'create_todos_table.sql')
            followups_migration = os.path.join(migrations_dir, 'create_followups_table.sql')
            
            # Run migrations
            print("\nRunning migrations...")
            success = True
            success &= run_migration(connection, todos_migration)
            success &= run_migration(connection, followups_migration)
            
            if success:
                print("\n✅ All migrations completed successfully!")
            else:
                print("\n❌ Some migrations failed. Check errors above.")
            
            # Verify tables were created
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            
            print(f"\nTables in database: {', '.join(tables)}")
            
            connection.close()
            
    except Error as e:
        print(f"❌ Error connecting to database: {e}")
        print("\nMake sure:")
        print("1. Cloud SQL Proxy is running (if using Cloud SQL)")
        print("2. Database credentials are correct in .env file")
        print("3. Database 'unified_inbox' exists")


if __name__ == "__main__":
    main()
