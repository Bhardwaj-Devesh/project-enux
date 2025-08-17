# Fork Features Implementation

## Overview
This implementation adds comprehensive fork functionality to the playbook system, including notifications, enhanced playbook views, and detailed fork tracking.

## New Features Implemented

### 1. Fork Notifications
- **API Endpoint**: `GET /api/v1/playbooks/notifications`
- **Count Endpoint**: `GET /api/v1/playbooks/notifications/count`
- **Purpose**: Shows when someone forks your playbook
- **Flow**: 
  - When User A forks User B's playbook
  - User B gets a notification showing "User A forked your playbook 'Title'"
  - Notifications are calculated dynamically (no new table needed)

### 2. Enhanced My Playbooks
- **API Endpoint**: `GET /api/v1/playbooks/my-playbooks-combined`
- **Purpose**: Shows both owned AND forked playbooks in one view
- **Features**:
  - Fork count for each playbook
  - "Forked" indicator for forked playbooks
  - Sorted by most recent activity

### 3. Separate Views
- **Owned Playbooks**: `GET /api/v1/playbooks/my-playbooks-enhanced`
- **Forked Playbooks**: `GET /api/v1/playbooks/my-forks`
- **Combined View**: `GET /api/v1/playbooks/my-playbooks-combined`

### 4. Playbook Details Enhancement
- **API Endpoint**: `GET /api/v1/playbooks/{playbook_id}/detailed`
- **Fork List**: `GET /api/v1/playbooks/{playbook_id}/forks`
- **Features**:
  - Shows total fork count
  - Lists users who forked the playbook
  - Detailed fork information

## API Endpoints

### Notifications
```http
GET /api/v1/playbooks/notifications?limit=20&offset=0
GET /api/v1/playbooks/notifications/count
```

### Enhanced Playbook Views
```http
GET /api/v1/playbooks/my-playbooks-enhanced?limit=50&offset=0
GET /api/v1/playbooks/my-forks?limit=50&offset=0
GET /api/v1/playbooks/my-playbooks-combined?limit=50&offset=0
```

### Detailed Playbook Information
```http
GET /api/v1/playbooks/{playbook_id}/detailed
GET /api/v1/playbooks/{playbook_id}/forks?limit=20&offset=0
```

## Data Models

### PlaybookWithForkInfo
```python
{
    "id": "uuid",
    "title": "string",
    "description": "string",
    "tags": ["string"],
    "stage": "string",
    "owner_id": "uuid",
    "version": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "fork_count": 5,           # Number of times forked
    "is_forked": true,         # Whether this is a forked playbook
    "forked_at": "datetime",   # When it was forked (if applicable)
    "original_playbook_id": "uuid"  # Original playbook ID (if forked)
}
```

### NotificationResponse
```python
{
    "type": "fork",
    "message": "John Doe forked your playbook 'My Playbook'",
    "playbook_id": "uuid",
    "playbook_title": "My Playbook",
    "user_id": "uuid",
    "user_email": "john@example.com",
    "user_full_name": "John Doe",
    "created_at": "datetime",
    "is_read": false
}
```

### PlaybookDetailedResponse
```python
{
    "id": "uuid",
    "title": "string",
    "description": "string",
    "tags": ["string"],
    "stage": "string",
    "owner_id": "uuid",
    "version": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "fork_count": 5,
    "forks": [
        {
            "user_id": "uuid",
            "user_email": "user@example.com",
            "user_full_name": "User Name",
            "forked_at": "datetime",
            "version": "v1"
        }
    ]
}
```

## Frontend Implementation Guide

### 1. Navigation Structure
```javascript
// Main navigation
const navigation = [
  { name: 'All Playbooks', href: '/playbooks' },
  { name: 'My Playbooks', href: '/my-playbooks' },  // Combined view
  { name: 'My Forks', href: '/my-forks' },          // Only forked
  { name: 'Notifications', href: '/notifications' }
];
```

### 2. My Playbooks Page
```javascript
// Fetch combined playbooks
const response = await fetch('/api/v1/playbooks/my-playbooks-combined');
const playbooks = await response.json();

// Display with fork indicators
playbooks.map(playbook => (
  <PlaybookCard 
    key={playbook.id}
    playbook={playbook}
    showForkBadge={playbook.is_forked}
    forkCount={playbook.fork_count}
  />
));
```

### 3. Notification Badge
```javascript
// Get notification count
const response = await fetch('/api/v1/playbooks/notifications/count');
const { count } = await response.json();

// Display badge
{count > 0 && <NotificationBadge count={count} />}
```

### 4. Playbook Detail Page
```javascript
// Fetch detailed playbook info
const response = await fetch(`/api/v1/playbooks/${playbookId}/detailed`);
const playbook = await response.json();

// Display fork information
<div>
  <h2>{playbook.title}</h2>
  <p>Forked {playbook.fork_count} times</p>
  {playbook.forks.length > 0 && (
    <div>
      <h3>Recent Forks</h3>
      {playbook.forks.map(fork => (
        <div key={fork.user_id}>
          {fork.user_full_name} forked on {fork.forked_at}
        </div>
      ))}
    </div>
  )}
</div>
```

## Database Queries

### Fork Count Query
```sql
SELECT COUNT(*) FROM user_playbooks 
WHERE original_playbook_id = 'playbook_id';
```

### User Notifications Query
```sql
SELECT up.*, u.email, u.full_name, p.title as playbook_title
FROM user_playbooks up
JOIN users u ON up.user_id = u.id
JOIN playbooks p ON up.original_playbook_id = p.id
WHERE p.owner_id = 'current_user_id'
ORDER BY up.forked_at DESC;
```

### Combined Playbooks Query
```sql
-- Owned playbooks with fork count
SELECT p.*, COUNT(up.id) as fork_count
FROM playbooks p
LEFT JOIN user_playbooks up ON p.id = up.original_playbook_id
WHERE p.owner_id = 'user_id'
GROUP BY p.id;

-- Forked playbooks
SELECT p.*, up.forked_at, up.id as user_playbook_id
FROM user_playbooks up
JOIN playbooks p ON up.original_playbook_id = p.id
WHERE up.user_id = 'user_id';
```

## Security Considerations

1. **RLS Policies**: All queries respect existing RLS policies
2. **User Validation**: Fork operations validate user existence
3. **Authorization**: Users can only see their own notifications and forked playbooks
4. **Data Privacy**: User information in fork lists is limited to public fields

## Performance Optimizations

1. **Efficient Queries**: Uses JOINs and COUNT operations for optimal performance
2. **Pagination**: All endpoints support limit/offset pagination
3. **Caching**: Consider caching fork counts for frequently accessed playbooks
4. **Indexing**: Ensure proper indexes on user_playbooks table

## Testing Scenarios

1. **Fork Creation**: User A forks User B's playbook
2. **Notification Generation**: User B receives notification
3. **Fork Count Update**: Playbook shows updated fork count
4. **Combined View**: User sees both owned and forked playbooks
5. **Detailed View**: Playbook page shows fork information
6. **Authorization**: Users can only access their own data

## Future Enhancements

1. **Real-time Notifications**: WebSocket integration for live updates
2. **Fork Analytics**: Detailed statistics about fork patterns
3. **Fork Collaboration**: Features for collaborating on forked playbooks
4. **Fork Sync**: Automatic syncing with original playbook updates
