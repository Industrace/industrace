#!/bin/bash

# Script to verify that no default secret values are used in configuration files
# This script checks docker-compose files and .env files for default/placeholder values

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "🔒 Checking for default secret values in configuration files..."
echo ""

# List of forbidden default values
FORBIDDEN_SECRETS=(
    "your-secret-key-change-in-production"
    "your-super-secret-jwt-key-change-in-production"
    "your-super-secret-secret-key-change-this-in-production"
    "your-encryption-key-here"
    "your-encryption-key-here-generate-with-command-above"
    "secure_password_123"
    "password"
    "changeme"
    "default"
    "secret"
)

# Files to check
COMPOSE_FILES=(
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "docker-compose.dev.yml"
    "docker-compose.custom-certs.yml"
)

ENV_FILES=(
    ".env"
    ".env.prod"
    ".env.prod-cloud"
    "custom-certs.env"
)

ENV_EXAMPLE_FILES=(
    ".env.example"
    "backend/production.env.example"
    "backend/development.env.example"
    "custom-certs.env.example"
)

check_file() {
    local file=$1
    local file_type=$2
    
    if [ ! -f "$file" ]; then
        return 0
    fi
    
    local found_issues=0
    local is_prod_file=false
    
    if [[ "$file" == *"prod"* ]] || [[ "$file" == *"custom-certs"* ]]; then
        is_prod_file=true
    fi
    
    # Check for hardcoded POSTGRES_PASSWORD (not using ${VAR} pattern)
    if grep -qiE "^\s*[^#]*POSTGRES_PASSWORD:\s*(secure_password|password|changeme|default)" "$file" 2>/dev/null; then
        # Check if it's NOT a variable substitution
        if ! grep -qiE "^\s*[^#]*POSTGRES_PASSWORD:\s*\$\{" "$file" 2>/dev/null; then
            echo -e "${RED}❌ ERROR${NC}: Found hardcoded POSTGRES_PASSWORD in ${file}"
            echo -e "   ${RED}→${NC} Use: POSTGRES_PASSWORD: \${DB_PASSWORD:-changeme}"
            grep -niE "^\s*[^#]*POSTGRES_PASSWORD:\s*(secure_password|password|changeme|default)" "$file" 2>/dev/null | while read -r line; do
                echo -e "   ${RED}→${NC} Line: $line"
            done
            found_issues=1
            ((ERRORS++))
        fi
    fi
    
    # Check for hardcoded SECRET_KEY (not using ${VAR} pattern)
    if grep -qiE "^\s*[^#]*-?\s*SECRET_KEY.*your-secret-key" "$file" 2>/dev/null; then
        echo -e "${RED}❌ ERROR${NC}: Found default SECRET_KEY in ${file}"
        echo -e "   ${RED}→${NC} Use: SECRET_KEY: \${SECRET_KEY}"
        grep -niE "^\s*[^#]*-?\s*SECRET_KEY.*your-secret-key" "$file" 2>/dev/null | while read -r line; do
            echo -e "   ${RED}→${NC} Line: $line"
        done
        found_issues=1
        ((ERRORS++))
    fi
    
    # For production files, check that SECRET_KEY and DB_PASSWORD don't use insecure fallbacks
    if [ "$is_prod_file" = true ]; then
        # Check for SECRET_KEY with changeme fallback
        if grep -qiE "SECRET_KEY.*\$\{SECRET_KEY:-changeme\}" "$file" 2>/dev/null; then
            echo -e "${RED}❌ ERROR${NC}: Found insecure SECRET_KEY fallback in production file: ${file}"
            echo -e "   ${RED}→${NC} Production files should require SECRET_KEY without fallback: SECRET_KEY: \${SECRET_KEY}"
            grep -niE "SECRET_KEY.*\$\{SECRET_KEY:-changeme\}" "$file" 2>/dev/null | while read -r line; do
                echo -e "   ${RED}→${NC} Line: $line"
            done
            found_issues=1
            ((ERRORS++))
        fi
        
        # Check for DB_PASSWORD with changeme fallback
        if grep -qiE "DB_PASSWORD:-changeme" "$file" 2>/dev/null; then
            echo -e "${RED}❌ ERROR${NC}: Found insecure DB_PASSWORD fallback in production file: ${file}"
            echo -e "   ${RED}→${NC} Production files should require DB_PASSWORD without fallback: \${DB_PASSWORD}"
            grep -niE "DB_PASSWORD:-changeme" "$file" 2>/dev/null | while read -r line; do
                echo -e "   ${RED}→${NC} Line: $line"
            done
            found_issues=1
            ((ERRORS++))
        fi
    fi
    
    # Check for hardcoded passwords in docker-compose files
    if [[ "$file_type" == "docker-compose" ]]; then
        # Check for POSTGRES_PASSWORD with hardcoded default values (exclude ${VAR:-default} patterns)
        # This regex matches POSTGRES_PASSWORD: followed by a value that is NOT a variable substitution
        if grep -qiE "POSTGRES_PASSWORD:\s*(secure_password|password|changeme|default)" "$file" 2>/dev/null; then
            # Check if it's a variable substitution pattern (${VAR} or ${VAR:-default})
            if ! grep -qiE "POSTGRES_PASSWORD:\s*\$\{" "$file" 2>/dev/null; then
                echo -e "${RED}❌ ERROR${NC}: Found hardcoded default POSTGRES_PASSWORD in ${file}"
                echo -e "   ${RED}→${NC} Use environment variable: POSTGRES_PASSWORD: \${DB_PASSWORD:-changeme}"
                grep -niE "POSTGRES_PASSWORD:\s*(secure_password|password|changeme|default)" "$file" 2>/dev/null | while read -r line; do
                    echo -e "   ${RED}→${NC} Line: $line"
                done
                found_issues=1
                ((ERRORS++))
            fi
        fi
        
        # For production files, check that SECRET_KEY uses variable substitution
        if [[ "$file" == *"prod"* ]] || [[ "$file" == *"custom-certs"* ]]; then
            if grep -qiE "SECRET_KEY.*your-secret-key" "$file" 2>/dev/null; then
                echo -e "${RED}❌ ERROR${NC}: Found default SECRET_KEY in production file: ${file}"
                echo -e "   ${RED}→${NC} Use environment variable: SECRET_KEY: \${SECRET_KEY}"
                grep -niE "SECRET_KEY.*your-secret-key" "$file" 2>/dev/null | while read -r line; do
                    echo -e "   ${RED}→${NC} Line: $line"
                done
                found_issues=1
                ((ERRORS++))
            fi
        fi
        
        # Check for SECRET_KEY with default values (not using ${SECRET_KEY})
        if grep -qiE "SECRET_KEY.*your-secret-key" "$file" 2>/dev/null; then
            echo -e "${RED}❌ ERROR${NC}: Found default SECRET_KEY in ${file}"
            grep -niE "SECRET_KEY.*your-secret-key" "$file" 2>/dev/null | while read -r line; do
                echo -e "   ${RED}→${NC} Line: $line"
            done
            found_issues=1
            ((ERRORS++))
        fi
    fi
    
    # Check for .env files with default values
    if [[ "$file_type" == "env" ]]; then
        # Check if SECRET_KEY is set to a default value
        if grep -qiE "^SECRET_KEY=.*(your-secret|changeme|default)" "$file" 2>/dev/null; then
            echo -e "${RED}❌ ERROR${NC}: Found default SECRET_KEY in ${file}"
            grep -niE "^SECRET_KEY=.*(your-secret|changeme|default)" "$file" 2>/dev/null | while read -r line; do
                echo -e "   ${RED}→${NC} Line: $line"
            done
            found_issues=1
            ((ERRORS++))
        fi
        
        # Check if ENCRYPTION_KEY is set to a default value (if not empty)
        if grep -qiE "^ENCRYPTION_KEY=.*(your-encryption|changeme|default)" "$file" 2>/dev/null; then
            echo -e "${RED}❌ ERROR${NC}: Found default ENCRYPTION_KEY in ${file}"
            grep -niE "^ENCRYPTION_KEY=.*(your-encryption|changeme|default)" "$file" 2>/dev/null | while read -r line; do
                echo -e "   ${RED}→${NC} Line: $line"
            done
            found_issues=1
            ((ERRORS++))
        fi
    fi
    
    return $found_issues
}

# Check docker-compose files
echo "📋 Checking docker-compose files..."
for file in "${COMPOSE_FILES[@]}"; do
    check_file "$file" "docker-compose"
done

# Check .env files (only if they exist)
echo ""
echo "📋 Checking .env files..."
for file in "${ENV_FILES[@]}"; do
    check_file "$file" "env"
done

# Check .env.example files for default values (warnings only)
echo ""
echo "📋 Checking .env.example files for default values..."
for file in "${ENV_EXAMPLE_FILES[@]}"; do
    if [ -f "$file" ]; then
        # Check if SECRET_KEY or ENCRYPTION_KEY have default values
        if grep -qiE "^SECRET_KEY=.*(your-secret|changeme|default)" "$file" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  WARNING${NC}: Found default SECRET_KEY in example file: ${file}"
            echo -e "   ${YELLOW}→${NC} This is OK for .example files, but ensure production .env files use secure values"
            ((WARNINGS++))
        fi
        if grep -qiE "^ENCRYPTION_KEY=.*(your-encryption|changeme|default)" "$file" 2>/dev/null && ! grep -qiE "^ENCRYPTION_KEY=\s*$" "$file" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  WARNING${NC}: Found default ENCRYPTION_KEY in example file: ${file}"
            echo -e "   ${YELLOW}→${NC} This is OK for .example files, but ensure production .env files use secure values"
            ((WARNINGS++))
        fi
    fi
done

# Check probe configuration files (must not be committed)
echo ""
echo "📋 Checking probe configuration files..."
PROBE_TRACKED=$(git ls-files 'probe/*.conf' 2>/dev/null | grep -v '\.example$' || true)
if [ -n "$PROBE_TRACKED" ]; then
    echo -e "${RED}❌ ERROR${NC}: Probe config files must not be tracked in git:"
    echo "$PROBE_TRACKED" | while read -r file; do
        echo -e "   ${RED}→${NC} ${file}"
        echo -e "   ${RED}→${NC} Use probe/probe.conf.example and keep local probe.conf out of version control"
    done
    ((ERRORS++))
fi

for file in probe/*.conf; do
    [ -f "$file" ] || continue
    [[ "$file" == *.example ]] && continue
    if grep -qiE '^\s*api_key\s*=\s*(your_api_key_here|test_api_key_123)\s*$' "$file" 2>/dev/null; then
        continue
    fi
    if grep -qiE '^\s*api_key\s*=\s*.+' "$file" 2>/dev/null; then
        if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
            echo -e "${RED}❌ ERROR${NC}: Real api_key found in tracked probe config: ${file}"
            ((ERRORS++))
        fi
    fi
done

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All security checks passed!${NC}"
    echo -e "${GREEN}   No default secret values found in production files.${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}   ${WARNINGS} warning(s) in .example files (these are OK).${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ Security check failed!${NC}"
    echo -e "${RED}   Found ${ERRORS} error(s) with default secret values.${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  ACTION REQUIRED:${NC}"
    echo -e "${YELLOW}   1. Review the errors above${NC}"
    echo -e "${YELLOW}   2. Replace all default values with secure, randomly generated values${NC}"
    echo -e "${YELLOW}   3. For SECRET_KEY, generate with: openssl rand -hex 32${NC}"
    echo -e "${YELLOW}   4. For ENCRYPTION_KEY, generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"${NC}"
    echo -e "${YELLOW}   5. For POSTGRES_PASSWORD, use a strong random password${NC}"
    echo ""
    exit 1
fi
