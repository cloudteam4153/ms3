from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from models import IncomingMessage, TaskCreate, Classification, TaskStatus, MessageType


class TaskListGenerator:
    """
    Processes LLM output organized by email/slack messages and extracts
    relevant tasks into cleaned dictionaries.
    """
    
    def __init__(self):
        self.due_date_keywords = {
            'today': 0,
            'tomorrow': 1,
            'asap': 0,
            'urgent': 0,
            'this week': 7,
            'next week': 14,
            'eod': 0,
            'eow': 7,
        }
    
    def generate_task_list(
        self, 
        messages: List[Dict[str, Any]], 
        user_id: int
    ) -> List[TaskCreate]:
        """
        Main method to convert LLM output into task creation objects.
        
        Args:
            messages: List of message dictionaries from LLM/Prioritizer
            user_id: ID of the user these tasks belong to
            
        Returns:
            List of TaskCreate objects ready for database insertion
        """
        tasks = []
        
        for msg_data in messages:
            try:
                message = IncomingMessage(**msg_data)
            except Exception as e:
                print(f"Invalid message format: {e}")
                continue
            
            if message.classification == Classification.NOISE:
                continue
            
            due_at = self._extract_due_date(message.task)
            clean_title = self._clean_task_title(message.task, message.classification)
            
            task = TaskCreate(
                user_id=user_id,
                source_msg_id=message.id,
                title=clean_title,
                status=TaskStatus.OPEN,
                due_at=due_at,
                priority=message.priority,
                message_type=message.type,
                sender=message.sender,
                subject=message.subject
            )
            
            tasks.append(task)
        
        return tasks
    
    def _extract_due_date(self, task_text: str) -> Optional[datetime]:
        """Extract due date from task text based on keywords"""
        task_lower = task_text.lower()
        
        for keyword, days_offset in self.due_date_keywords.items():
            if keyword in task_lower:
                return datetime.now() + timedelta(days=days_offset)
        
        date_pattern = r'\b(\d{1,2})/(\d{1,2})\b'
        match = re.search(date_pattern, task_text)
        if match:
            try:
                month, day = int(match.group(1)), int(match.group(2))
                year = datetime.now().year
                due_date = datetime(year, month, day)
                
                if due_date < datetime.now():
                    due_date = datetime(year + 1, month, day)
                
                return due_date
            except ValueError:
                pass
        
        return None
    
    def _clean_task_title(self, task_text: str, classification: Classification) -> str:
        """Clean and format task title for better readability"""
        prefixes_to_remove = [
            'task:', 'todo:', 'action item:', 
            'follow up:', 'followup:', 'reply to'
        ]
        
        clean_text = task_text.strip()
        for prefix in prefixes_to_remove:
            if clean_text.lower().startswith(prefix):
                clean_text = clean_text[len(prefix):].strip()
        
        if classification == Classification.FOLLOWUP:
            if not clean_text.lower().startswith('reply'):
                clean_text = f"Reply: {clean_text}"
        
        if clean_text:
            clean_text = clean_text[0].upper() + clean_text[1:]
        
        if len(clean_text) > 200:
            clean_text = clean_text[:197] + "..."
        
        return clean_text
    