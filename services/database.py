import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, pooling
from typing import List, Optional
import time
from models import (
    TaskCreate, TaskUpdate, TaskResponse, TaskStatus,
    TodoCreate, TodoUpdate, TodoResponse,
    FollowupCreate, FollowupUpdate, FollowupResponse
)
from datetime import datetime

load_dotenv()


class DatabaseManager:
    """Handles all database operations for the Actions Service with connection pooling"""
    
    # Class-level connection pool (shared across instances)
    _pool = None
    _pool_config = None
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self._initialize_pool()
    
    def _get_pool_config(self):
        """Get connection pool configuration based on environment"""
        if self._pool_config:
            return self._pool_config
        
        # Check if using Cloud SQL (Unix socket connection)
        cloud_sql_connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
        unix_socket_path = os.getenv('DB_UNIX_SOCKET')
        
        config = {
            'database': os.getenv('DB_NAME', 'unified_inbox'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'autocommit': False,
            'pool_name': 'actions_service_pool',
            'pool_size': int(os.getenv('DB_POOL_SIZE', 5)),  # Default 5 connections
            'pool_reset_session': True,
        }
        
        if cloud_sql_connection_name and unix_socket_path:
            # Cloud SQL via Unix socket (when running on GCP/Cloud Run)
            config['unix_socket'] = unix_socket_path
            config['connect_timeout'] = 10  # Timeout for Unix socket connections too
            print(f"Configuring connection pool for Cloud SQL via Unix socket: {cloud_sql_connection_name}")
        else:
            # Standard TCP connection (local or Cloud SQL via TCP)
            config['host'] = os.getenv('DB_HOST', 'localhost')
            config['port'] = int(os.getenv('DB_PORT', 3306))
            config['connect_timeout'] = 10
            print(f"Configuring connection pool for MySQL at {config['host']}:{config['port']}")
        
        self._pool_config = config
        return config
    
    def _initialize_pool(self, retry_count=0):
        """Initialize connection pool with retry logic"""
        try:
            if self._pool is None:
                config = self._get_pool_config()
                self._pool = mysql.connector.pooling.MySQLConnectionPool(**config)
                print(f"Connection pool initialized with {config['pool_size']} connections")
        except Error as e:
            print(f"Error initializing connection pool (attempt {retry_count + 1}/{self.max_retries}): {e}")
            
            # Retry logic for production
            if retry_count < self.max_retries - 1:
                print(f"Retrying pool initialization in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                return self._initialize_pool(retry_count + 1)
            else:
                print("Max retries reached. Connection pool initialization failed.")
                self._pool = None
    
    def _get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            self._initialize_pool()
        
        if self._pool is None:
            return None
        
        try:
            connection = self._pool.get_connection()
            if connection.is_connected():
                return connection
            else:
                # Connection is not valid, try to get another one
                return self._pool.get_connection()
        except Error as e:
            print(f"Error getting connection from pool: {e}")
            # Try to reinitialize pool
            self._pool = None
            self._initialize_pool()
            if self._pool:
                try:
                    return self._pool.get_connection()
                except Error:
                    return None
            return None
    
    def ensure_connection(self):
        """Ensure we can get a connection from the pool"""
        connection = self._get_connection()
        return connection is not None
    
    def _execute_query(self, query_func):
        """Helper method to execute queries with proper connection handling"""
        connection = self._get_connection()
        if connection is None:
            return None
        
        try:
            result = query_func(connection)
            return result
        except Error as e:
            print(f"Database error: {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                connection.close()  # Return connection to pool

    
    def create_task(self, task):
        """Insert a new task into the tasks table and return its ID."""
        connection = self._get_connection()
        if connection is None:
            return None

        try:
            query = """
                INSERT INTO tasks (
                    user_id,
                    source_msg_id,
                    title,
                    status,
                    due_at,
                    priority,
                    message_type,
                    sender,
                    subject
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # If status is an enum, convert to its value
            status_value = (
                task.status.value if hasattr(task.status, "value") else task.status
            )

            # If message_type is an enum, convert to its value
            message_type_value = (
                task.message_type.value
                if hasattr(task.message_type, "value")
                else task.message_type
            )

            values = (
                task.user_id,
                task.source_msg_id,
                task.title,
                status_value or "open",
                task.due_at,
                task.priority or 1,
                message_type_value or "email",
                task.sender,
                task.subject,
            )

            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
            task_id = cursor.lastrowid
            cursor.close()
            return task_id

        except Error as e:
            print(f"Error creating task: {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                connection.close()


    def get_task(self, task_id: int) -> Optional[TaskResponse]:
        """Retrieve a single task by ID"""
        connection = self._get_connection()
        if connection is None:
            return None
            
        query = """
        SELECT task_id, user_id, source_msg_id, title, status, due_at, 
               priority, message_type, sender, subject, created_at, updated_at
        FROM tasks
        WHERE task_id = %s
        """
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (task_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return TaskResponse(**result)
            return None
        except Error as e:
            print(f"Error fetching task: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    
    def get_tasks(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None,
        min_priority: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[List[TaskResponse], int]:
        """Retrieve tasks with optional filters + pagination"""
        connection = self._get_connection()
        if connection is None:
            return [], 0

        # Base WHERE clause
        where_clause = "WHERE user_id = %s"
        params = [user_id]

        if status:
            where_clause += " AND status = %s"
            params.append(status.value)

        if min_priority:
            where_clause += " AND priority >= %s"
            params.append(min_priority)

        # 1) Get total count (for pagination metadata)
        count_query = f"""
        SELECT COUNT(*) AS total
        FROM tasks
        {where_clause}
        """

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(count_query, params)
            count_row = cursor.fetchone()
            total = count_row["total"] if count_row else 0
            cursor.close()
        except Error as e:
            print(f"Error counting tasks: {e}")
            if connection.is_connected():
                connection.close()
            return [], 0

        # 2) Get the actual page of results
        query = f"""
        SELECT task_id, user_id, source_msg_id, title, status, due_at,
               priority, message_type, sender, subject, created_at, updated_at
        FROM tasks
        {where_clause}
        ORDER BY priority DESC, due_at ASC
        LIMIT %s OFFSET %s
        """

        page_params = params + [limit, offset]

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, page_params)
            results = cursor.fetchall()
            cursor.close()

            tasks = [TaskResponse(**row) for row in results]
            return tasks, total
        except Error as e:
            print(f"Error fetching tasks: {e}")
            return [], total
        finally:
            if connection.is_connected():
                connection.close()

    def update_task(self, task_id: int, updates: TaskUpdate) -> bool:
        """Update a task with new values"""
        connection = self._get_connection()
        if connection is None:
            return False
            
        update_fields = []
        params = []
        
        if updates.title is not None:
            update_fields.append("title = %s")
            params.append(updates.title)
        
        if updates.status is not None:
            update_fields.append("status = %s")
            params.append(updates.status.value)
        
        if updates.due_at is not None:
            update_fields.append("due_at = %s")
            params.append(updates.due_at)
        
        if updates.priority is not None:
            update_fields.append("priority = %s")
            params.append(updates.priority)
        
        if not update_fields:
            if connection.is_connected():
                connection.close()
            return False
        
        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(task_id)
        
        query = f"""
        UPDATE tasks 
        SET {', '.join(update_fields)}
        WHERE task_id = %s
        """
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error updating task: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID"""
        connection = self._get_connection()
        if connection is None:
            return False
            
        query = "DELETE FROM tasks WHERE task_id = %s"
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, (task_id,))
            connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error deleting task: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    # ========== TODO METHODS ==========
    
    def create_todo(self, todo: TodoCreate) -> Optional[int]:
        """Insert a new todo into the todos table and return its ID."""
        connection = self._get_connection()
        if connection is None:
            return None

        try:
            query = """
                INSERT INTO todos (
                    user_id,
                    source_msg_id,
                    title,
                    status,
                    due_at,
                    priority,
                    message_type,
                    sender,
                    subject
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # If status is an enum, convert to its value
            status_value = (
                todo.status.value if hasattr(todo.status, "value") else todo.status
            )

            # If message_type is an enum, convert to its value
            message_type_value = (
                todo.message_type.value
                if hasattr(todo.message_type, "value")
                else todo.message_type
            )

            values = (
                todo.user_id,
                todo.source_msg_id,
                todo.title,
                status_value or "open",
                todo.due_at,
                todo.priority or 1,
                message_type_value or "email",
                todo.sender,
                todo.subject,
            )

            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
            todo_id = cursor.lastrowid
            cursor.close()
            return todo_id

        except Error as e:
            print(f"Error creating todo: {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                connection.close()

    def get_todo(self, todo_id: int) -> Optional[TodoResponse]:
        """Retrieve a single todo by ID"""
        connection = self._get_connection()
        if connection is None:
            return None
            
        query = """
        SELECT todo_id, user_id, source_msg_id, title, status, due_at, 
               priority, message_type, sender, subject, created_at, updated_at
        FROM todos
        WHERE todo_id = %s
        """
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (todo_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return TodoResponse(**result)
            return None
        except Error as e:
            print(f"Error fetching todo: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    
    def get_todos(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None,
        min_priority: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[List[TodoResponse], int]:
        """Retrieve todos with optional filters + pagination"""
        connection = self._get_connection()
        if connection is None:
            return [], 0

        # Base WHERE clause
        where_clause = "WHERE user_id = %s"
        params = [user_id]

        if status:
            where_clause += " AND status = %s"
            params.append(status.value)

        if min_priority:
            where_clause += " AND priority >= %s"
            params.append(min_priority)

        # 1) Get total count (for pagination metadata)
        count_query = f"""
        SELECT COUNT(*) AS total
        FROM todos
        {where_clause}
        """

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(count_query, params)
            count_row = cursor.fetchone()
            total = count_row["total"] if count_row else 0
            cursor.close()
        except Error as e:
            print(f"Error counting todos: {e}")
            if connection.is_connected():
                connection.close()
            return [], 0

        # 2) Get the actual page of results
        query = f"""
        SELECT todo_id, user_id, source_msg_id, title, status, due_at,
               priority, message_type, sender, subject, created_at, updated_at
        FROM todos
        {where_clause}
        ORDER BY priority DESC, due_at ASC
        LIMIT %s OFFSET %s
        """

        page_params = params + [limit, offset]

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, page_params)
            results = cursor.fetchall()
            cursor.close()

            todos = [TodoResponse(**row) for row in results]
            return todos, total
        except Error as e:
            print(f"Error fetching todos: {e}")
            return [], total
        finally:
            if connection.is_connected():
                connection.close()

    def update_todo(self, todo_id: int, updates: TodoUpdate) -> bool:
        """Update a todo with new values"""
        connection = self._get_connection()
        if connection is None:
            return False
            
        update_fields = []
        params = []
        
        if updates.title is not None:
            update_fields.append("title = %s")
            params.append(updates.title)
        
        if updates.status is not None:
            update_fields.append("status = %s")
            params.append(updates.status.value)
        
        if updates.due_at is not None:
            update_fields.append("due_at = %s")
            params.append(updates.due_at)
        
        if updates.priority is not None:
            update_fields.append("priority = %s")
            params.append(updates.priority)
        
        if not update_fields:
            if connection.is_connected():
                connection.close()
            return False
        
        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(todo_id)
        
        query = f"""
        UPDATE todos 
        SET {', '.join(update_fields)}
        WHERE todo_id = %s
        """
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error updating todo: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo by ID"""
        connection = self._get_connection()
        if connection is None:
            return False
            
        query = "DELETE FROM todos WHERE todo_id = %s"
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, (todo_id,))
            connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error deleting todo: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                connection.close()

    # ========== FOLLOWUP METHODS ==========
    
    def create_followup(self, followup: FollowupCreate) -> Optional[int]:
        """Insert a new followup into the followups table and return its ID."""
        connection = self._get_connection()
        if connection is None:
            return None

        try:
            query = """
                INSERT INTO followups (
                    user_id,
                    source_msg_id,
                    title,
                    status,
                    due_at,
                    priority,
                    message_type,
                    sender,
                    subject
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # If status is an enum, convert to its value
            status_value = (
                followup.status.value if hasattr(followup.status, "value") else followup.status
            )

            # If message_type is an enum, convert to its value
            message_type_value = (
                followup.message_type.value
                if hasattr(followup.message_type, "value")
                else followup.message_type
            )

            values = (
                followup.user_id,
                followup.source_msg_id,
                followup.title,
                status_value or "open",
                followup.due_at,
                followup.priority or 1,
                message_type_value or "email",
                followup.sender,
                followup.subject,
            )

            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
            followup_id = cursor.lastrowid
            cursor.close()
            return followup_id

        except Error as e:
            print(f"Error creating followup: {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                connection.close()

    def get_followup(self, followup_id: int) -> Optional[FollowupResponse]:
        """Retrieve a single followup by ID"""
        connection = self._get_connection()
        if connection is None:
            return None
            
        query = """
        SELECT followup_id, user_id, source_msg_id, title, status, due_at, 
               priority, message_type, sender, subject, created_at, updated_at
        FROM followups
        WHERE followup_id = %s
        """
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (followup_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return FollowupResponse(**result)
            return None
        except Error as e:
            print(f"Error fetching followup: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    
    def get_followups(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None,
        min_priority: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[List[FollowupResponse], int]:
        """Retrieve followups with optional filters + pagination"""
        connection = self._get_connection()
        if connection is None:
            return [], 0

        # Base WHERE clause
        where_clause = "WHERE user_id = %s"
        params = [user_id]

        if status:
            where_clause += " AND status = %s"
            params.append(status.value)

        if min_priority:
            where_clause += " AND priority >= %s"
            params.append(min_priority)

        # 1) Get total count (for pagination metadata)
        count_query = f"""
        SELECT COUNT(*) AS total
        FROM followups
        {where_clause}
        """

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(count_query, params)
            count_row = cursor.fetchone()
            total = count_row["total"] if count_row else 0
            cursor.close()
        except Error as e:
            print(f"Error counting followups: {e}")
            if connection.is_connected():
                connection.close()
            return [], 0

        # 2) Get the actual page of results
        query = f"""
        SELECT followup_id, user_id, source_msg_id, title, status, due_at,
               priority, message_type, sender, subject, created_at, updated_at
        FROM followups
        {where_clause}
        ORDER BY priority DESC, due_at ASC
        LIMIT %s OFFSET %s
        """

        page_params = params + [limit, offset]

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, page_params)
            results = cursor.fetchall()
            cursor.close()

            followups = [FollowupResponse(**row) for row in results]
            return followups, total
        except Error as e:
            print(f"Error fetching followups: {e}")
            return [], total
        finally:
            if connection.is_connected():
                connection.close()

    def update_followup(self, followup_id: int, updates: FollowupUpdate) -> bool:
        """Update a followup with new values"""
        connection = self._get_connection()
        if connection is None:
            return False
            
        update_fields = []
        params = []
        
        if updates.title is not None:
            update_fields.append("title = %s")
            params.append(updates.title)
        
        if updates.status is not None:
            update_fields.append("status = %s")
            params.append(updates.status.value)
        
        if updates.due_at is not None:
            update_fields.append("due_at = %s")
            params.append(updates.due_at)
        
        if updates.priority is not None:
            update_fields.append("priority = %s")
            params.append(updates.priority)
        
        if not update_fields:
            if connection.is_connected():
                connection.close()
            return False
        
        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(followup_id)
        
        query = f"""
        UPDATE followups 
        SET {', '.join(update_fields)}
        WHERE followup_id = %s
        """
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error updating followup: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def delete_followup(self, followup_id: int) -> bool:
        """Delete a followup by ID"""
        connection = self._get_connection()
        if connection is None:
            return False
            
        query = "DELETE FROM followups WHERE followup_id = %s"
        
        try:
            cursor = connection.cursor()
            cursor.execute(query, (followup_id,))
            connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error deleting followup: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                connection.close()
    
    def close(self):
        """Close connection pool (connections are managed by the pool)"""
        # With connection pooling, we don't need to close individual connections
        # The pool manages them. This method is kept for backward compatibility.
        if self._pool:
            print("Connection pool is active (connections managed by pool)")
            