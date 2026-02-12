# API Documentation

Industrace provides a comprehensive REST API built with FastAPI and OpenAPI standards for managing industrial control system assets and configurations.

## API Overview

### Development Environment
- **Base URL**: `http://localhost:8000`
- **OpenAPI Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Production Environment
- **Base URL**: `https://industrace.local/api`
- **OpenAPI Documentation**: `https://industrace.local/api/docs`
- **ReDoc Documentation**: `https://industrace.local/api/redoc`
- **OpenAPI JSON**: `https://industrace.local/api/openapi.json`

### Custom Certificates Environment
- **Base URL**: `https://yourdomain.com/api`
- **OpenAPI Documentation**: `https://yourdomain.com/api/docs`
- **ReDoc Documentation**: `https://yourdomain.com/api/redoc`
- **OpenAPI JSON**: `https://yourdomain.com/api/openapi.json`

**Version**: 2.0.0 (see [Release Notes](release-notes.md) for full API coverage)

## Authentication

The API uses JWT-based authentication with HTTP-only cookies:

1. **Login**: `POST /login` with email and password
2. **Cookie**: JWT token is automatically set as a cookie
3. **Session**: All subsequent requests use the cookie for authentication

### Login Example
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@example.com&password=password123" \
  -c cookies.txt
```

## Core Endpoints

### System Endpoints

#### Health Check
```http
GET /health
```
Returns system health status and version information.

#### Setup Status
```http
GET /setup/status
```
Returns system configuration status and statistics.

### Asset Management

#### List Assets
```http
GET /assets?limit=10&offset=0&search=server
```

#### Get Asset by ID
```http
GET /assets/{asset_id}
```

#### Create Asset
```http
POST /assets
Content-Type: application/json

{
  "name": "Production Server",
  "asset_type_id": "uuid",
  "location_id": "uuid",
  "description": "Main production server"
}
```

#### Update Asset
```http
PUT /assets/{asset_id}
```

#### Delete Asset
```http
DELETE /assets/{asset_id}
```

### User Management

#### List Users
```http
GET /users
```

#### Create User
```http
POST /users
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "role_id": "uuid",
  "tenant_id": "uuid"
}
```

#### Get Current User
```http
GET /users/me
```

### Search and Filtering

#### Global Search
```http
GET /search/global?q=server
```

#### Asset Search with Filters
```http
GET /assets?status_id=uuid&site_id=uuid&risk_level=high
```

## Response Format

### Standard Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

### Error Response
```json
{
  "detail": "INVALID_CREDENTIALS",
  "error_code": "AUTH_001"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid credentials |
| `AUTH_002` | Expired token |
| `PERM_001` | Insufficient permissions |
| `VAL_001` | Invalid input data |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource conflict |

## Rate Limiting

The API implements rate limiting to protect against abuse:
- **Default**: 100 requests/hour
- **Strict**: 10 requests/minute for sensitive endpoints

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

Most list endpoints support pagination:

```http
GET /assets?page=1&size=20&offset=0
```

Parameters:
- `page`: Page number (1-based)
- `size`: Items per page (max 1000)
- `offset`: Skip items (alternative to page)

## Filtering and Sorting

### Filtering
```http
GET /assets?status=active&site_id=uuid&risk_level=high
```

### Sorting
```http
GET /assets?sort_by=name&sort_order=desc
```

## File Uploads

### Upload Asset Photo
```http
POST /assets/{asset_id}/photos
Content-Type: multipart/form-data

file: [binary data]
```

### Upload Asset Document
```http
POST /assets/{asset_id}/documents
Content-Type: multipart/form-data

file: [binary data]
description: "Technical documentation"
```

## Bulk Operations

### Bulk Update Assets
```http
POST /assets/bulk-update
Content-Type: application/json

{
  "asset_ids": ["uuid1", "uuid2"],
  "updates": {
    "status_id": "new-status-uuid",
    "site_id": "new-site-uuid"
  }
}
```

### Bulk Soft Delete
```http
POST /assets/bulk-soft-delete
Content-Type: application/json

{
  "asset_ids": ["uuid1", "uuid2"]
}
```

## Testing the API

### Using cURL
```bash
# Health check
curl http://localhost:8000/health

# Login and save cookies
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@example.com&password=password123" \
  -c cookies.txt

# Use authenticated session
curl http://localhost:8000/assets -b cookies.txt
```

### Using Python
```python
import requests

# Login
session = requests.Session()
response = session.post('http://localhost:8000/login', data={
    'email': 'admin@example.com',
    'password': 'password123'
})

# Use session for authenticated requests
assets = session.get('http://localhost:8000/assets').json()
```

### Using Swagger UI
1. Open `http://localhost:8000/docs`
2. Click "Authorize" to enter credentials
3. Test endpoints directly from the interface

## SDK and Client Libraries

### Python Client Example
```python
from industrace_client import IndustraceClient

client = IndustraceClient('http://localhost:8000')
client.login('admin@example.com', 'password123')

assets = client.get_assets(limit=10)
```

## Best Practices

1. **Always handle errors**: Check response status codes
2. **Use pagination**: For large datasets, use pagination
3. **Cache when appropriate**: Cache static data like asset types
4. **Rate limiting**: Respect rate limits and implement backoff
5. **Security**: Never expose credentials in client-side code
6. **Validation**: Validate data before sending to API

## Support

For API support:
1. Check the OpenAPI documentation at `/docs`
2. Review error codes and messages
3. Check system logs for detailed error information
4. Verify authentication and permissions 