# Development Roadmap

## Overview

This roadmap outlines the development path for Industrace, the Configuration Management Database for Industrial Control Systems. The focus is on stability, documentation, and community growth.

## Delivered in v2.0 (June 2026)

The following major features were delivered in version 2.0:

- **ISA/IEC 62443 Compliance**: Security zones, conduits, security requirements, capabilities, SR assessments, evidence
- **Vulnerability Intelligence**: CVE management, vulnerability feeds, automatic matching, risk integration
- **Asset Dependencies and Review**: Dependency graph, risk propagation, asset review and maintenance scheduling
- **Notification System**: Templates, queue, logs, user preferences, email integration
- **Single Sign-On (SSO)**: Azure AD / Microsoft Entra ID integration
- **Extended RBAC**: New permission sections for all new modules; see [ADMINISTRATION.md](ADMINISTRATION.md#role-based-access-control-rbac)
- **Password Policy**: Stricter requirements (12+ chars, complexity); see [ADMINISTRATION.md](ADMINISTRATION.md#password-policy)
- **Asset Detail Redesign**: New layout with tabs for Security, Dependencies, Vulnerabilities, IEC 62443, Review

See [Release Notes](release-notes.md) and [CHANGELOG](../CHANGELOG.md) for full details.

## Current Priorities

### Multi-Deployment Support ✅
- **Development**: Vite dev server with hot-reload
- **Production**: Traefik + Let's Encrypt for automatic SSL
- **Custom Certificates**: Nginx + custom SSL certificates
- **Automatic Configuration**: CORS, cookies, and security settings

### Documentation and Support
- Complete user documentation
- Installation and configuration guides
- FAQ and troubleshooting
- Multi-deployment documentation

### Security Enhancements
- Multi-Factor Authentication (MFA) implementation
- TOTP-based authentication for web users
- Backup codes for account recovery
- Enhanced security audit logging

### Mobile Strategy
- Responsive web application design
- Touch-optimized user interface
- Mobile-first navigation and layout
- Progressive Web App (PWA) implementation

### Stability and Performance
- Performance optimizations
- Security improvements
- Bug fixes and maintenance
- Regression testing

## Future Considerations

### Potential Improvements
- Advanced reporting features
- External system integrations
- Customizable workflows
- Native mobile applications (if required)

### Technology Evolution
- Architecture improvements
- Database optimizations
- API enhancements
- PWA capabilities (offline support, push notifications)

## Goals

### Technical
- Stability and reliability
- Optimal performance
- Robust security
- Easy maintenance
- Mobile accessibility

### Community
- Complete documentation
- Active support
- Organic growth
- Continuous feedback

## Conclusion

This roadmap prioritizes stability and community growth over complex new features. The focus is on documentation, support, and incremental improvements based on user feedback. Mobile strategy focuses on responsive web design and PWA capabilities rather than native applications, providing the best balance of functionality, cost, and maintenance.

---

**Industrace** - Configuration Management Database for Industrial Control Systems  
**Author**: Maurizio Bertaboni
**Website**: https://besafe.it/industrace  
**Contact**: industrace@besafe.it

*Last Updated: June 2026* 