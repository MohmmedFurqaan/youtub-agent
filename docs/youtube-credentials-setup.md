# YouTube API Credentials Setup

This guide explains how to configure the Google OAuth credentials required by the YouTube Agent.

> **Important:** You do not need to download `credentials.json`.  
> The project loads the required OAuth configuration from the `.env` file.

---

## Prerequisites

You need:

- A Google account
- Access to the YouTube channel where videos will be uploaded
- Access to the project's Google Cloud project, or permission to create one

---

## 1. Open Google Cloud Console

Open:

https://console.cloud.google.com/

Sign in with your Google account.

Create a new Google Cloud project or select the existing project used by the YouTube Agent.

Example:

```text
Project name:
youtube-agent
```

---

## 2. Enable YouTube Data API v3

Inside the selected Google Cloud project:

1. Open **APIs & Services**.
2. Click **Library**.
3. Search for:

```text
YouTube Data API v3
```

4. Open **YouTube Data API v3**.
5. Click **Enable**.

This API is required because the application uploads videos using the YouTube Data API.

---

## 3. Configure OAuth

Open:

**Google Cloud Console → Google Auth Platform**

Configure the OAuth consent screen if Google asks you to do so.

Use the project/application information provided by the project owner.

For example:

```text
App name:
YouTube Agent

User support email:
Your Google account

Developer contact:
Your Google account
```

If the application is configured for testing, make sure the Google account that will authorize the YouTube upload is allowed as a test user.

---

## 4. Create an OAuth Client

Go to:

**Google Cloud Console → Google Auth Platform → Clients**

Click:

**Create Client**

For the application type, select:

```text
Desktop app
```

Use a name such as:

```text
YouTube Agent
```

Click **Create**.

---

## 5. Get the OAuth Values

After creating the OAuth client, Google will provide information similar to:

```text
Client ID:
123456789-xxxxxxxxxxxxxxxx.apps.googleusercontent.com

Client Secret:
GOCSPX-xxxxxxxxxxxxxxxx

Project ID:
youtube-agent-123456
```

We will use these values in the project's `.env` file.

### Do not download or commit `credentials.json`

The project does not require a `credentials.json` file.

---

## 6. Configure `.env`

In the root of the YouTube Agent project, create:

```text
.env
```

Add:

```env
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_PROJECT_ID=your_project_id

YOUTUBE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
YOUTUBE_TOKEN_URI=https://oauth2.googleapis.com/token
YOUTUBE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
YOUTUBE_REDIRECT_URI=http://localhost
```

Replace:

```text
your_client_id
your_client_secret
your_project_id
```

with the values from Google Cloud.

---

## 7. Protect `.env`

Never commit the real `.env` file to Git.

Make sure `.gitignore` contains:

```gitignore
.env
```

The repository can contain:

```text
.env.example
```

with empty values:

```env
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_PROJECT_ID=

YOUTUBE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
YOUTUBE_TOKEN_URI=https://oauth2.googleapis.com/token
YOUTUBE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
YOUTUBE_REDIRECT_URI=http://localhost
```

Each developer should create their own `.env` from `.env.example`.

---

## 8. How the Authentication Works

The credentials in `.env` identify the application.

When the YouTube Agent runs, Google OAuth asks the user to authorize access to the YouTube account.

The flow is:

```text
.env
  │
  │ Client ID + Client Secret
  ▼
YouTube Agent
  │
  │ OAuth 2.0
  ▼
Google Login
  │
  │ User grants permission
  ▼
YouTube Account
```

The application uses the following OAuth scope:

```text
https://www.googleapis.com/auth/youtube.upload
```

This permission is required to upload videos.

---

## 9. Running the Application

This project uses `uv`.

After configuring `.env`, run the application using the project's normal entry point.

For example:

```bash
uv run python youtube_uploader.py
```

The application should start the Google OAuth flow.

A browser window will open.

Sign in using the Google account that owns or manages the YouTube channel.

Approve the requested permission.

---

## 10. Credential Checklist

Before running the application, verify:

- [ ] Google Cloud project selected
- [ ] YouTube Data API v3 enabled
- [ ] OAuth consent screen configured
- [ ] Desktop OAuth client created
- [ ] Client ID copied to `.env`
- [ ] Client Secret copied to `.env`
- [ ] Project ID copied to `.env`
- [ ] `.env` added to `.gitignore`
- [ ] YouTube account is authorized/test user if required
- [ ] Application started with `uv`

---

## Security

Never share or commit:

```text
.env
```

Do not put the following into GitHub:

```text
YOUTUBE_CLIENT_SECRET
```

If the client secret is accidentally committed or publicly exposed, inform the project owner and rotate the credential in Google Cloud.

---

## Official Google Resources

Google Cloud Console:

https://console.cloud.google.com/

YouTube Data API:

https://developers.google.com/youtube/v3

YouTube Video Upload Guide:

https://developers.google.com/youtube/v3/guides/uploading_a_video

YouTube API Authentication:

https://developers.google.com/youtube/v3/guides/authentication
