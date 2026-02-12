# SSO Configuration Guide with Azure AD (Microsoft 365)

This guide will help you configure Single Sign-On (SSO) authentication between Industrace and Azure AD (Microsoft 365 / Entra ID).

## Prerequisites

- Administrator access to Microsoft Azure Portal
- Administrator access to Industrace
- Active Microsoft 365 / Azure AD tenant

## Step 1: Register the Application in Azure AD

### 1.1 Sign in to Azure Portal

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with a tenant administrator account
3. Navigate to **Azure Active Directory** (or **Microsoft Entra ID**)

### 1.2 Register a New Application

1. In the left menu, select **App registrations**
2. Click **+ New registration**
3. Fill in the form:
   - **Name**: `Industrace SSO` (or a name of your choice)
   - **Supported account types**:
     - Select **Accounts in this organizational directory only** for maximum security
     - Or **Accounts in any organizational directory** if you need to support multiple tenants
   - **Redirect URI**:
     - Platform: **Web**
     - URI: `https://yourdomain.com/api/auth/sso/azure_ad/callback`
     - ⚠️ **IMPORTANT**: Replace `yourdomain.com` with your actual domain
     - Example: `https://industrace.local/api/auth/sso/azure_ad/callback` (for local development)
     - Example: `https://app.industrace.com/api/auth/sso/azure_ad/callback` (for production)
4. Click **Register**

### 1.3 Note the Application Information

After registration, note the following:

- **Application (client) ID**: This is your `Client ID`
- **Directory (tenant) ID**: This is your `Tenant Domain` (you can also use the tenant name, e.g. `contoso.onmicrosoft.com`)

## Step 2: Configure Authentication

### 2.1 Configure Redirect URIs

1. On the application page, go to **Authentication**
2. Under **Redirect URIs**, add:
   - `https://yourdomain.com/api/auth/sso/azure_ad/callback`
   - `https://yourdomain.com/api/auth/sso/azure_ad/authorize` (optional, for direct redirect)
3. Under **Implicit grant and hybrid flows**, ensure:
   - ✅ **ID tokens** is selected (required for OIDC)
   - ❌ **Access tokens** can be unchecked (not required for the base flow)
4. Click **Save**

### 2.2 Configure API Permissions

1. Go to **API permissions**
2. Verify the following are present:
   - **Microsoft Graph** > **openid** (Delegated) - ✅ Already present
   - **Microsoft Graph** > **profile** (Delegated) - ✅ Already present
   - **Microsoft Graph** > **email** (Delegated) - ✅ Already present
   - **Microsoft Graph** > **User.Read** (Delegated) - Add if not present
3. **IMPORTANT**: If you need to import users, also add:
   - **Microsoft Graph** > **User.Read.All** (Application) - ⚠️ **REQUIRED** to import users
   - This permission must be of type **Application** (not Delegated) to work with the client credentials flow
   - ⚠️ **Requires admin consent**
4. Click **Grant admin consent** - **REQUIRED** for Application permissions
5. ⚠️ **Note**: Without **User.Read.All (Application)** permission and admin consent, user import will not work

## Step 3: Create a Client Secret

### 3.1 Generate the Secret

1. Go to **Certificates & secrets**
2. Under **Client secrets**, click **+ New client secret**
3. Fill in:
   - **Description**: `Industrace SSO Secret` (or a descriptive name)
   - **Expires**: Choose an expiry (recommended: 24 months for production)
4. Click **Add**
5. ⚠️ **IMPORTANT**: Copy the **Value** of the secret immediately (you will only see it once!)
   - This is your `Client Secret`

## Step 4: Configure Industrace

### 4.1 Access SSO Configuration

1. Log in to Industrace as an administrator
2. Go to **SSO Config**
3. If no configuration exists yet, click **Start Setup**

### 4.2 Fill in the Configuration Form

Fill in the following fields:

- **Provider Type**: Select `Azure AD (EntraID)`
- **Enabled**: Enable when you are ready to test
- **Client ID**: Paste the **Application (client) ID** from Step 1.3
- **Client Secret**: Paste the **Value** of the secret from Step 3.1
- **Tenant Domain**:
  - You can use the **Directory (tenant) ID** (UUID)
  - Or the tenant name (e.g. `contoso.onmicrosoft.com`)
  - Or `common` to support personal Microsoft accounts (not recommended for enterprise)
- **Redirect URI**:
  - Must match exactly what is configured in Azure AD
  - Example: `https://yourdomain.com/api/auth/sso/azure_ad/callback`
- **Auto-Provisioning**:
  - ⚠️ **Recommended: DISABLED** for maximum security
  - If disabled, only users who already exist in Industrace can sign in
  - Existing users are linked automatically if the email matches
- **Domain Restriction** (optional):
  - Example: `contoso.com` to allow only users from this domain

### 4.3 Test the Connection

1. Click **Test Connection**
2. If the test succeeds, proceed to the next step
3. If it fails, verify:
   - Client ID and Client Secret are correct
   - Redirect URI matches exactly
   - API permissions are configured correctly

### 4.4 Save the Configuration

1. Click **Save**
2. Enable **Enabled** if you have not already
3. The configuration is now active!

## Step 5: Import Users (Optional)

### 5.1 Import Users from Azure AD

1. On the SSO Config page, go to the **Import Users** tab
2. Search for users you want to import (you can filter by name or email)
3. Select the users to import
4. Choose the **Role** to assign to the imported users
5. Click **Import Selected**

### 5.2 Verify Imported Users

1. Go to **Users** in Industrace
2. Verify that the users were created correctly
3. Imported users will have:
   - Email matching the one in Azure AD
   - Role assigned during import
   - `auth_provider` set to `azure_ad`

## Step 6: Test SSO Login

### 6.1 Test Login

1. Log out of Industrace
2. Go to the login page
3. You should see a **"Sign in with Microsoft"** button (or similar)
4. Click the button
5. You will be redirected to Microsoft for authentication
6. After authentication, you will be redirected back to Industrace automatically

### 6.2 Verify User Linking

1. After SSO login, go to **Profile**
2. Verify that the user was linked correctly:
   - The user should have `auth_provider` = `azure_ad`
   - The user should have `external_id` populated

## Troubleshooting

### Issue: "Invalid redirect URI"

**Cause**: The Redirect URI in Industrace does not match the one configured in Azure AD.

**Solution**:
- Verify that the Redirect URI in Industrace matches exactly the one in Azure AD
- Check for extra spaces or special characters
- Ensure the protocol is correct (http vs https)

### Issue: "Invalid client secret"

**Cause**: The Client Secret has expired or is incorrect.

**Solution**:
- Generate a new Client Secret in Azure AD
- Update the configuration in Industrace with the new secret

### Issue: "User not found" during login

**Cause**: The user does not exist in Industrace and auto-provisioning is disabled.

**Solution**:
- Import the user manually via the "Import Users" feature
- Or enable auto-provisioning (not recommended for security)

### Issue: "Domain restriction violation"

**Cause**: The user's email does not match the domain configured in Domain Restriction.

**Solution**:
- Verify the user's domain in Azure AD
- Update Domain Restriction to include the correct domain
- Or remove Domain Restriction if not needed

### Issue: SSO button does not appear on the login page

**Cause**: SSO configuration is not enabled or is not configured correctly.

**Solution**:
- Verify that **Enabled** is turned on in the SSO configuration
- Verify that the configuration was saved correctly
- Check backend logs for any errors

### Issue: Error 500 when listing/importing Azure AD users

**Cause**: The Azure AD application does not have the correct permissions or admin consent has not been granted.

**Solution**:
1. Verify that **User.Read.All (Application)** permission has been added (not Delegated!)
2. Verify that **admin consent** has been granted (Grant admin consent)
3. Check backend logs for the specific error:
   - If you see "Failed to authenticate" → issue with Client ID/Secret or tenant
   - If you see "Insufficient privileges" → User.Read.All (Application) permission is missing
   - If you see "consent required" → admin consent is missing
4. After adding permissions, wait a few minutes before retrying (Azure AD may take time to propagate permissions)

## Important Notes

### Security

- ⚠️ **Never share the Client Secret**: It is a sensitive credential
- ⚠️ **Use HTTPS in production**: The Redirect URI must use HTTPS
- ⚠️ **Auto-provisioning disabled**: Recommended for maximum security
- ⚠️ **Domain Restriction**: Use to limit access to specific domains

### Best Practices

1. **Test in a development environment before production**
2. **Use long-expiry secrets** (24 months) to avoid disruption
3. **Document the configuration** for your team
4. **Monitor logs** for any issues
5. **Rotate secrets** before they expire

## Support

For issues or questions:
- See Azure AD documentation: [https://docs.microsoft.com/azure/active-directory/](https://docs.microsoft.com/azure/active-directory/)
- Contact Industrace support
