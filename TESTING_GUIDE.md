# Testing Guide for Phases 2-5

This guide helps you test the implemented functionality: Data Models, Database Layer, API Endpoints, and Classification Webhook.

## Prerequisites

1. **Cloud SQL Proxy must be running** (if using Cloud SQL):
   ```bash
   ./cloud-sql-proxy unified-inbox-480816:us-central1:unified-inbox-db
   ```

2. **Environment variables configured** in `.env`:
   ```bash
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=unified_inbox
   DB_USER=root
   DB_PASSWORD=your_password
   ```

3. **Start the FastAPI server**:
   ```bash
   python3 main.py
   # Or
   uvicorn main:app --reload --port 8004
   ```

   Server will be available at: `http://localhost:8004`
   API docs at: `http://localhost:8004/docs`

## Testing Phase 4: API Endpoints (CRUD Operations)

### Test 1: Create a Todo

```bash
curl -X POST "http://localhost:8004/todo" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "source_msg_id": 101,
    "title": "Review project proposal",
    "status": "open",
    "priority": 3,
    "message_type": "email",
    "sender": "john@example.com",
    "subject": "Project Proposal Review"
  }'
```

**Expected**: Returns 201 with todo details including `todo_id`

### Test 2: Get a Todo by ID

```bash
curl "http://localhost:8004/todo/1"
```

**Expected**: Returns 200 with todo details + HATEOAS links

### Test 3: List Todos with Filters

```bash
# Get all todos for user 1
curl "http://localhost:8004/todo?user_id=1"

# Filter by status
curl "http://localhost:8004/todo?user_id=1&status=open"

# Filter by minimum priority
curl "http://localhost:8004/todo?user_id=1&priority=3"
```

**Expected**: Returns 200 with list of todos

### Test 4: Update a Todo

```bash
curl -X PUT "http://localhost:8004/todo/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "done",
    "priority": 2
  }'
```

**Expected**: Returns 200 with updated todo

### Test 5: Delete a Todo

```bash
curl -X DELETE "http://localhost:8004/todo/1"
```

**Expected**: Returns 204 (No Content)

### Test 6-10: Repeat for Followups

Replace `/todo` with `/followup` in all above commands:

```bash
# Create followup
curl -X POST "http://localhost:8004/followup" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "source_msg_id": 102,
    "title": "Reply: Meeting follow-up",
    "status": "open",
    "priority": 4,
    "message_type": "slack",
    "sender": "jane@example.com",
    "subject": "Meeting notes"
  }'

# Get followup
curl "http://localhost:8004/followup/1"

# List followups
curl "http://localhost:8004/followup?user_id=1"

# Update followup
curl -X PUT "http://localhost:8004/followup/1" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'

# Delete followup
curl -X DELETE "http://localhost:8004/followup/1"
```

## Testing Phase 5: Classification Webhook

### Test: Process Classifications

```bash
curl -X POST "http://localhost:8004/classifications/webhook?user_id=1" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": 201,
      "type": "email",
      "subject": "Action Required: Budget Review",
      "sender": "finance@example.com",
      "classification": "todo",
      "task": "Review Q4 budget proposal by end of week",
      "priority": 5
    },
    {
      "id": 202,
      "type": "slack",
      "subject": null,
      "sender": "team-lead@example.com",
      "classification": "followup",
      "task": "Reply to team meeting invitation",
      "priority": 3
    },
    {
      "id": 203,
      "type": "email",
      "subject": "Project Update",
      "sender": "pm@example.com",
      "classification": "noise",
      "task": "FYI: Project status update",
      "priority": 1
    }
  ]'
```

**Expected Response**:
```json
{
  "message": "Classifications processed successfully",
  "created": {
    "tasks_count": 0,
    "todos_count": 1,
    "followups_count": 1
  },
  "items": {
    "tasks": [],
    "todos": [...],
    "followups": [...]
  }
}
```

**What should happen**:
- Message 201 (TODO) → Creates a todo
- Message 202 (FOLLOWUP) → Creates a followup
- Message 203 (NOISE) → Skipped (not created)

## Testing via Swagger UI (Easier!)

1. Open browser: `http://localhost:8004/docs`
2. You'll see all endpoints with interactive forms
3. Click "Try it out" on any endpoint
4. Fill in the request body/parameters
5. Click "Execute"

This is the easiest way to test!

## Verify Database Directly

If you want to verify data was created in the database:

```bash
# Connect through Cloud SQL Proxy
mysql -h 127.0.0.1 -u root -p unified_inbox

# Then run SQL queries:
SELECT * FROM todos;
SELECT * FROM followups;
SELECT * FROM tasks;
```

## Test Scenarios

### Scenario 1: Complete Todo Lifecycle
1. Create todo
2. Get todo by ID
3. Update todo (mark as done)
4. List todos (verify status changed)
5. Delete todo

### Scenario 2: Classification Processing
1. Send webhook with mixed classifications
2. Verify todos created for TODO classification
3. Verify followups created for FOLLOWUP classification
4. Verify NOISE messages are skipped

### Scenario 3: Filtering and Pagination
1. Create multiple todos with different priorities
2. Test filtering by status
3. Test filtering by minimum priority
4. Verify results are ordered correctly

## Common Issues

### Issue: "Can't connect to MySQL server"
**Solution**: Make sure Cloud SQL Proxy is running

### Issue: "Failed to create todo (DB error)"
**Solution**: 
- Check database connection in `.env`
- Verify tables exist: `SHOW TABLES;` in MySQL
- Check server logs for detailed error

### Issue: "422 Unprocessable Entity"
**Solution**: Check request body format matches the model:
- Required fields are present
- Enum values are correct (`"open"` or `"done"`, not `"OPEN"`)
- Priority is between 1-5

### Issue: "404 Not Found"
**Solution**: 
- Verify the ID exists in database
- Check you're using the correct endpoint path

## Quick Test Script

Save this as `test_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8004"

echo "=== Testing Todo CRUD ==="

# Create
echo "Creating todo..."
TODO_RESPONSE=$(curl -s -X POST "$BASE_URL/todo" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "source_msg_id": 999,
    "title": "Test Todo",
    "priority": 3,
    "message_type": "email",
    "sender": "test@example.com"
  }')

TODO_ID=$(echo $TODO_RESPONSE | grep -o '"todo_id":[0-9]*' | grep -o '[0-9]*')
echo "Created todo ID: $TODO_ID"

# Get
echo "Getting todo..."
curl -s "$BASE_URL/todo/$TODO_ID" | python3 -m json.tool

# Update
echo "Updating todo..."
curl -s -X PUT "$BASE_URL/todo/$TODO_ID" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}' | python3 -m json.tool

# List
echo "Listing todos..."
curl -s "$BASE_URL/todo?user_id=1" | python3 -m json.tool

echo "=== Testing Classification Webhook ==="
curl -s -X POST "$BASE_URL/classifications/webhook?user_id=1" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": 888,
      "type": "email",
      "sender": "test@example.com",
      "classification": "todo",
      "task": "Test classification",
      "priority": 2
    }
  ]' | python3 -m json.tool
```

Make it executable and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

## Next Steps

After testing phases 2-5, you can proceed to:
- Phase 6: Integrations Service Integration
- Phase 7: Cloud SQL Configuration
- Phase 8: Cloud Run Deployment
