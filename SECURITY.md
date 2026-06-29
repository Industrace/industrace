# Security Policy

## Supported Versions

We release security patches for the following versions:

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 2.1.x   | :white_check_mark: | Current stable line |
| 2.0.x   | :white_check_mark: | Security fixes only |
| 1.x     | :x:                | Frozen — upgrade to 2.x |
| < 1.0   | :x:                | |

**Current release:** v2.1.0 (June 2026)

For production deployments, see [Pilot Deployment Checklist](docs/PILOT_DEPLOYMENT_CHECKLIST.md) and [Configuration Guide](docs/CONFIGURATION.md).

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in Industrace, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **industrace@besafe.it**

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact and affected components
- **Environment**: Version, operating system, and configuration details
- **Proof of Concept**: If applicable, include a minimal proof of concept

### Response Timeline

- **Acknowledgment**: Within 48 hours of receiving your report
- **Initial Assessment**: Within 7 days
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days
- **Disclosure**: Coordinated disclosure after patch is available

## Security Best Practices

### For System Administrators

#### Production Deployment
- **Always use HTTPS** in production environments
- **Set `SETUP_TOKEN`** before exposing a fresh instance (required in production)
- **Disable API docs** (`EXTERNAL_API_DOCS_ENABLED=false`) unless needed for internal debugging
- **Configure `CORS_ORIGINS`** with your real domain(s) — never use `*` in production
- **Enable SSL/TLS** with strong cipher suites
- **Use strong, unique passwords** for all accounts
- **Implement proper firewall rules** to restrict access
- **Regular security updates** for the underlying operating system
- **Database encryption** at rest and in transit
- **Regular backups** with encryption and off-site storage

#### Access Control
- **Multi-factor authentication** (MFA) for administrative accounts
- **Role-based access control** (RBAC) with principle of least privilege
- **Regular access reviews** and user account audits
- **Session management** with appropriate timeouts
- **API key rotation** for external integrations

#### Monitoring and Logging
- **Enable audit logging** for all critical operations
- **Monitor failed login attempts** and suspicious activities
- **Set up alerts** for security events
- **Regular log review** and analysis
- **Intrusion detection** systems where appropriate

### For Developers

#### Code Security
- **Input validation** for all user inputs
- **SQL injection prevention** using parameterized queries
- **Cross-site scripting (XSS) prevention** with proper output encoding
- **Cross-site request forgery (CSRF) protection**
- **Secure file upload** handling with validation
- **Dependency scanning** for known vulnerabilities

#### Authentication and Authorization
- **Strong password policies** enforcement
- **Secure session management** with proper tokens
- **JWT authentication** via HttpOnly secure cookies (Bearer header supported for API clients)
- **RBAC enforcement** on API endpoints by permission section and level
- **Setup wizard protection** via `X-Setup-Token` header when `SETUP_TOKEN` is configured
- **API authentication** using secure methods
- **Permission checks** at every endpoint

#### Data Protection
- **Encryption of sensitive data** at rest and in transit
- **Personal data protection** compliance (GDPR, etc.)
- **Secure data transmission** using TLS 1.2+
- **Data anonymization** for logs and analytics
- **Secure data disposal** procedures

## Security Features

### Built-in Security Measures

- **Role-based access control** with granular permissions
- **Audit trail** for all system operations
- **Data encryption** for sensitive information
- **Secure API endpoints** with authentication
- **Input validation** and sanitization
- **CSRF protection** for web forms
- **Session security** with secure cookies

### Network Security

- **HTTPS enforcement** in production
- **CORS configuration** for API security
- **Rate limiting** to prevent abuse
- **Request validation** and filtering
- **Secure headers** implementation

## Vulnerability Disclosure

### Coordinated Disclosure Process

1. **Report**: Security researcher reports vulnerability privately
2. **Acknowledge**: We acknowledge receipt within 48 hours
3. **Investigate**: We investigate and assess the vulnerability
4. **Develop Fix**: We develop and test a security patch
5. **Release**: We release the patch and security advisory
6. **Credit**: We credit the researcher (if desired)

### Security Advisories

Security advisories are published on:
- **GitHub Security Advisories**
- **Project documentation**
- **Release notes**

## Security Updates

### Regular Updates
- **Monthly security patches** for non-critical issues
- **Immediate patches** for critical vulnerabilities
- **Security dependency updates** as needed
- **Regular security reviews** of the codebase

### Update Process
1. **Test** patches in development environment
2. **Validate** security fixes thoroughly
3. **Document** changes and impact
4. **Release** with clear upgrade instructions
5. **Monitor** for any issues post-deployment

## Compliance and Standards

### Security Standards
- **OWASP Top 10** compliance
- **ISO 27001** security management principles
- **NIST Cybersecurity Framework** alignment
- **Industrial security** best practices

### Data Protection
- **GDPR compliance** for EU users
- **Data minimization** principles
- **Right to be forgotten** implementation
- **Data breach notification** procedures

## Contact Information

- **Security Email**: industrace@besafe.it
- **Documentation**: [Project Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/Industrace/industrace/issues)

## Acknowledgments

We thank the security community for their responsible disclosure of vulnerabilities. Security researchers who follow our coordinated disclosure process will be acknowledged in our security advisories.

---

**Last Updated**: June 2026  
**Version**: 2.1  
**License**: AGPL v3
