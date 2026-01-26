# strava_ics
link strava activity to calendar


# 🏃‍♂️ Strava to Calendar Auto-Sync (Serverless)

This project automatically syncs your recent Strava activities to a `.ics` calendar file using **GitHub Actions**. It runs on a schedule, fetches your data via the Strava API, and updates a calendar subscription file that you can add to Google Calendar, Apple Calendar, or Outlook.

**Tech Stack:**
* **Python** (Scripting)
* **GitHub Actions** (Automation/Cron)
* **uv** (Ultra-fast Python package installer & caching)
* **Strava API** (Data source)

---

## 📋 Prerequisites

1.  A free **Strava** account.
2.  A **GitHub** account.
3.  Basic familiarity with the terminal.

---

## 🚀 Setup Guide

### Phase 1: Strava API Configuration

1.  Log in to [Strava API Settings](https://www.strava.com/settings/api).
2.  Create an Application.
    * **Important:** You **MUST** upload an icon/image for your app, otherwise Strava hides the API keys.
    * **Authorization Callback Domain:** Set this to `localhost`.
3.  Once created, copy your **Client ID** and **Client Secret**.

### Phase 2: The OAuth 2.0 "Handshake" (The Tricky Part)

You need a **Refresh Token** so the script can log in permanently without your help.

1.  **Get the Authorization Code:**
    Replace `[YOUR_CLIENT_ID]` in the URL below and paste it into your browser:
    ```
    [https://www.strava.com/oauth/authorize?client_id=](https://www.strava.com/oauth/authorize?client_id=)[YOUR_CLIENT_ID]&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all
    ```
2.  Click **Authorize**. You will be redirected to a broken page (`localhost`).
3.  Look at the URL bar. Copy the code after `&code=`.
    * *Example:* `...&code=a1b2c3d4e5f6...&scope=...` (Copy only `a1b2c3d4e5f6`).

4.  **Exchange Code for Refresh Token:**
    Run this command in your terminal (replace the values):
    ```bash
    curl -X POST [https://www.strava.com/oauth/token](https://www.strava.com/oauth/token) \
      -F client_id=[YOUR_CLIENT_ID] \
      -F client_secret=[YOUR_CLIENT_SECRET] \
      -F code=[CODE_FROM_STEP_3] \
      -F grant_type=authorization_code
    ```
5.  In the JSON response, copy the `"refresh_token"`.

### Phase 3: GitHub Repository Setup

1.  Create a new **Public** repository on GitHub (Private repos block calendar services from reading the `.ics` file).
2.  Go to **Settings** > **Secrets and variables** > **Actions**.
3.  Add the following Repository Secrets:
    * `STRAVA_CLIENT_ID`
    * `STRAVA_CLIENT_SECRET`
    * `STRAVA_REFRESH_TOKEN`




📅 Final Step: Subscribe to Calendar
Wait for the Action to run successfully (Green checkmark ✅).

Go to your repository Code tab.

Click on the newly created strava.ics file.

Click the "Raw" button.

Copy the URL (It starts with https://raw.githubusercontent.com/...).

Paste this URL into your calendar app:

Google Calendar: Settings > Add Calendar > From URL.

Apple Calendar: File > New Calendar Subscription.

Note: If Google Calendar fails to fetch the URL, ensure your Repository Visibility is set to Public in Settings > General > Danger Zone.