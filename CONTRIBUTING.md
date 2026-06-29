# Contributing to Industrace

Thank you for your interest in contributing to Industrace! 🎉

This document provides guidelines for contributing to the Industrace project, a comprehensive industrial asset management system.

## 📋 Table of Contents

- [How to Contribute](#how-to-contribute)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Code Guidelines](#code-guidelines)
- [Testing](#testing)
- [Contribution Process](#contribution-process)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)
- [Frequently Asked Questions](#frequently-asked-questions)

## 🤝 How to Contribute

There are many ways to contribute to Industrace:

- 🐛 **Bug Reports**: If you find a bug, report it!
- 💡 **Feature Requests**: Suggest new features
- 📝 **Documentation**: Improve documentation
- 🔧 **Code**: Contribute bug fixes and new features
- 🧪 **Testing**: Help test the software
- 🌍 **Translations**: Contribute to translations

## 🛠️ Development Environment Setup

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Docker and Docker Compose**
- **Git**

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/industrace/industrace.git
   cd industrace
   ```

2. **Start development environment**
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

3. **Add demo data** (optional, on an initialized system)
   ```bash
   make demo
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Database: PostgreSQL on port 5432

For a production-like local stack with HTTPS, use `make prod` instead.

### Tenant Management

When creating a new tenant, the system automatically initializes:

- **Default Roles**: admin, editor, viewer with appropriate permissions
- **Admin User**: First user with admin privileges
- **Tenant Isolation**: Complete data separation between tenants

**Example:**
```bash
make create-tenant TENANT_NAME="My Company" TENANT_SLUG="my-company" ADMIN_EMAIL="admin@mycompany.com"
```

### Useful Make Commands

```bash
docker compose -f docker-compose.dev.yml up -d   # Start development environment
make prod          # Start production-like stack (HTTPS, Nginx)
make test          # Run backend tests in Docker
make demo          # Add demo data to running prod stack
make logs          # View production logs
make clean         # Clean system completely
make shell         # Open backend shell
make migrate       # Run database migrations
make rebuild       # Rebuild containers
make help          # Show all commands
```

## 📁 Project Structure

```
industrace/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── models/         # SQLAlchemy Models
│   │   ├── schemas/        # Pydantic Schemas
│   │   ├── routers/        # API Endpoints
│   │   ├── crud/          # Database Operations
│   │   ├── services/      # Business Logic
│   │   └── utils.py       # Utilities
│   ├── tests/             # Backend Tests
│   └── requirements.txt   # Python Dependencies
├── frontend/              # Vue.js 3 Frontend
│   ├── src/
│   │   ├── components/    # Vue Components
│   │   ├── pages/        # App Pages
│   │   ├── api/          # API Client
│   │   └── composables/  # Vue Composables
│   ├── tests/            # Frontend Tests
│   └── package.json      # Node.js Dependencies
├── docs/                 # Documentation
├── scripts/              # Utility Scripts
└── docker-compose*.yml   # Docker Configurations
```

## 📝 Code Guidelines

### Python (Backend)

- **Version**: Python 3.8+
- **Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Formatting**: Black, isort
- **Linting**: flake8

#### Conventions

```python
# Function and variable names in snake_case
def get_asset_by_id(asset_id: int) -> Asset:
    pass

# Class names in PascalCase
class AssetService:
    pass

# Constants in UPPER_CASE
DEFAULT_PAGE_SIZE = 50

# Type hints required
def create_asset(asset_data: AssetCreate, user_id: int) -> Asset:
    pass
```

### JavaScript/Vue.js (Frontend)

- **Version**: Node.js 16+
- **Framework**: Vue.js 3
- **UI Library**: PrimeVue
- **Build Tool**: Vite
- **Testing**: Vitest

#### Conventions

```javascript
// Function names in camelCase
function getAssetById(assetId) {
    return assets.find(asset => asset.id === assetId);
}

// Component names in PascalCase
// AssetList.vue
export default {
    name: 'AssetList',
    // ...
}

// Variable names in camelCase
const assetData = ref(null);
```

### Database

- **System**: PostgreSQL
- **Migrations**: Alembic
- **Naming**: snake_case for tables and columns

```sql
-- Example conventions
CREATE TABLE asset_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

### Backend Testing

```bash
# Run all tests with coverage (recommended — uses Docker)
make test

# Run specific tests inside the backend container
docker compose -f docker-compose.dev.yml run --rm --no-deps \
  -e DATABASE_URL=sqlite:///:memory: \
  -e SECRET_KEY=test-secret-key \
  -e ENVIRONMENT=development \
  backend pytest tests/test_rbac_section_access.py -v
```

### Frontend Testing

```bash
cd frontend
npm run test:unit
npm run build
```

### Testing Guidelines

- Write tests for all new features
- Backend coverage is reported in CI and via `make test` (progressive improvement target)
- Use parameterized tests when appropriate
- Test both success and error cases

## 🔄 Contribution Process

### 1. Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally
3. Add the upstream repository

```bash
git clone https://github.com/your-username/industrace.git
cd industrace
git remote add upstream https://github.com/industrace/industrace.git
```

### 2. Create a Branch

Create a new branch for your feature/bugfix:

```bash
git checkout -b feature/new-feature
# or
git checkout -b fix/bug-description
```

### 3. Develop

- Write code following the guidelines
- Add appropriate tests
- Update documentation if necessary
- Commit frequently with descriptive messages

### 4. Commit Guidelines

Use Conventional Commits format:

```
type(scope): description

feat(auth): add two-factor authentication
fix(assets): resolve asset deletion bug
docs(api): update API documentation
test(backend): add user service tests
```

Available types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Refactoring
- `test`: Test
- `chore`: Build, config, etc.

### 5. Push and Pull Request

```bash
git push origin feature/new-feature
```

Create a Pull Request on GitHub with:

- **Descriptive title**: E.g., "Add two-factor authentication"
- **Detailed description**: Explain what the PR does
- **Issue reference**: Link to related issues
- **Screenshots**: If applicable
- **Checklist**: Confirm you've completed all steps

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation
- [ ] Test

## Testing
- [ ] I ran tests locally
- [ ] Tests pass
- [ ] I added tests for new functionality

## Checklist
- [ ] Code follows project guidelines
- [ ] I updated documentation
- [ ] Changes are backward compatible
- [ ] I linked related issues

## Screenshots (if applicable)
```

## 🐛 Bug Reports

Before reporting a bug:

1. **Search existing issues** to see if it's already reported
2. **Reproduce the bug** in a clean environment
3. **Gather information** useful for debugging

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of the bug

## Reproduction Steps
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
Description of what should happen

## Screenshots
Screenshots if applicable

## Environment
- OS: [e.g. macOS 14.0]
- Browser: [e.g. Chrome 120]
- Industrace Version: [e.g. v1.0.0]

## Logs
Error logs if available
```

## 💡 Feature Requests

### Feature Request Template

```markdown
## Description
Clear and concise description of the requested feature

## Motivation
Why this feature is useful

## Proposed Solution
Description of desired solution

## Alternatives Considered
Other solutions considered

## Additional Information
Screenshots, mockups, or other information
```

## ❓ Frequently Asked Questions

### How can I contribute if I'm not a developer?

- **Documentation**: Improve guides, tutorials, README
- **Testing**: Test new features and report bugs
- **Translations**: Contribute to translations
- **Feedback**: Provide feedback on UX/UI

### How do I handle merge conflicts?

```bash
# Update your branch with upstream
git fetch upstream
git rebase upstream/main

# Resolve conflicts if necessary
# Then push
git push origin feature/your-branch --force-with-lease
```

### How can I get help?

- **GitHub Issues**: Open an issue for questions
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check documentation in `/docs`

### What are the commit policies?

- Use Conventional Commits
- Commit frequently
- Each commit should be functionally complete
- Write clear and descriptive commit messages

## 📞 Contact

- **Repository**: https://github.com/industrace/industrace
- **Issues**: https://github.com/industrace/industrace/issues
- **Email**: industrace@besafe.it
- **Website**: https://besafe.it/industrace

## 📄 License

By contributing to Industrace, you agree that your changes will be released under the [AGPL-3.0](LICENSE) license.

---

Thank you for contributing to Industrace! 🚀

Every contribution, big or small, is appreciated and helps make Industrace better for everyone.
