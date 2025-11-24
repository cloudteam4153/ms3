import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from typing import List, Optional
from models import TaskCreate, TaskUpdate, TaskResponse, TaskStatus
from datetime import datetime

load_dotenv()


class DatabaseManager:
    """Handles all database operations for the Actions Service"""
    
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'unified_inbox'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                port=int(os.getenv('DB_PORT', 3306))
            )
            if self.connection.is_connected():
                print("Successfully connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None

    
    def create_task(self, task):
        """Insert a new task into the tasks table and return its ID."""
        if not self.connection:
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

            cursor = self.connection.cursor()
            cursor.execute(query, values)
            self.connection.commit()
            task_id = cursor.lastrowid
            cursor.close()
            return task_id

        except Error as e:
            print(f"Error creating task: {e}")
            return None


    def get_task(self, task_id: int) -> Optional[TaskResponse]:
        """Retrieve a single task by ID"""
        if not self.connection:
            return None
            
        query = """
        SELECT task_id, user_id, source_msg_id, title, status, due_at, 
               priority, message_type, sender, subject, created_at, updated_at
        FROM tasks
        WHERE task_id = %s
        """
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (task_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return TaskResponse(**result)
            return None
        except Error as e:
            print(f"Error fetching task: {e}")
            return None
    
    def get_tasks(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None,
        min_priority: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[List[TaskResponse], int]:
        """Retrieve tasks with optional filters + pagination"""
        if not self.connection:
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
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(count_query, params)
            count_row = cursor.fetchone()
            total = count_row["total"] if count_row else 0
            cursor.close()
        except Error as e:
            print(f"Error counting tasks: {e}")
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
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, page_params)
            results = cursor.fetchall()
            cursor.close()

            tasks = [TaskResponse(**row) for row in results]
            return tasks, total
        except Error as e:
            print(f"Error fetching tasks: {e}")
            return [], total

    def update_task(self, task_id: int, updates: TaskUpdate) -> bool:
        """Update a task with new values"""
        if not self.connection:
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
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error updating task: {e}")
            self.connection.rollback()
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID"""
        if not self.connection:
            return False
            
        query = "DELETE FROM tasks WHERE task_id = %s"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (task_id,))
            self.connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            print(f"Error deleting task: {e}")
            self.connection.rollback()
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
            