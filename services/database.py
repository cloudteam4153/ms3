import os
from typing import Optional, List
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from models import TaskCreate, TaskResponse, TaskUpdate, TaskStatus


class DatabaseManager:
    """Handles all database operations for the Actions Service"""
    
    def __init__(self):
        self.connection = None
        # Comment this out if you don't have MySQL set up yet
        # self.connect()
    
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
            raise
    
    def create_task(self, task: TaskCreate) -> Optional[int]:
        """Insert a new task into the database"""
        if not self.connection:
            print("No database connection")
            return None
            
        query = """
        INSERT INTO tasks 
        (user_id, source_msg_id, title, status, due_at, priority, 
         message_type, sender, subject, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        values = (
            task.user_id,
            task.source_msg_id,
            task.title,
            task.status.value,
            task.due_at,
            task.priority,
            task.message_type.value,
            task.sender,
            task.subject,
            now,
            now
        )
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, values)
            self.connection.commit()
            task_id = cursor.lastrowid
            cursor.close()
            return task_id
        except Error as e:
            print(f"Error creating task: {e}")
            self.connection.rollback()
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
        min_priority: Optional[int] = None
    ) -> List[TaskResponse]:
        """Retrieve tasks with optional filters"""
        if not self.connection:
            return []
            
        query = """
        SELECT task_id, user_id, source_msg_id, title, status, due_at,
               priority, message_type, sender, subject, created_at, updated_at
        FROM tasks
        WHERE user_id = %s
        """
        params = [user_id]
        
        if status:
            query += " AND status = %s"
            params.append(status.value)
        
        if min_priority:
            query += " AND priority >= %s"
            params.append(min_priority)
        
        query += " ORDER BY priority DESC, due_at ASC"
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            
            return [TaskResponse(**row) for row in results]
        except Error as e:
            print(f"Error fetching tasks: {e}")
            return []
    
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
            