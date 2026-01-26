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




## 🛠️ How to use this for YOUR Strava data

Want to run this for yourself? You don't need to write any code!

### 1. Fork the Repository
Click the **Fork** button (top right of this page). This creates an exact copy of this project in your own GitHub account.



### 2. Clean up (Remove my data)
Since you forked my project, you also got my calendar file. You need to delete it:
1. In your forked repository, click on the `strava.ics` file.
2. Click the **Trash can icon** 🗑️ (Delete file) at the top right.
3. Click **Commit changes**.

### 3. Add your API Keys
You need your own Strava credentials (follow the "Setup Guide" above to get your Client ID, Secret, and Refresh Token).
1. Go to your repository **Settings**.
2. Go to **Secrets and variables** > **Actions**.
3. Create the 3 repository secrets with your own values:
   * `STRAVA_CLIENT_ID`
   * `STRAVA_CLIENT_SECRET`
   * `STRAVA_REFRESH_TOKEN`

### 4. Enable and Run
By default, GitHub disables Actions on forked repositories for security.
1. Go to the **Actions** tab.
2. Click the green button **"I understand my workflows, go ahead and enable them"**.
3. Select the **Update Strava Calendar** workflow on the left.
4. Click **Run workflow** > **Run workflow**.

Wait 30 seconds... and a new `strava.ics` file will appear in your code, generated from YOUR Strava activities! 🚀




# 🔒 Update: Privacy Mode (Secret Gist Integration)

This project has been updated to support **maximum privacy**.

Previously, the repository had to be **Public** for calendar apps (Google/Apple) to read the `.ics` file.
Now, the script pushes the calendar data to a **Secret Gist**. This allows you to:
1. Keep this repository **Private** (hiding your code and history).
2. Generate an obfuscated, "secret" URL for your calendar that cannot be guessed or searched.

---

## 🛠️ Configuration Guide

If you want to switch to this private mode, follow these steps:

### Step 1: Generate a GitHub Token
The script needs permission to write to your Gists.
1. Go to your GitHub **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2. Click **Generate new token (classic)**.
3. **Note:** "Strava Gist Sync".
4. **Expiration:** Select **"No expiration"** (important!).
5. **Scopes:** Check only the box for **`gist`**.
6. Click **Generate**.
7. ⚠️ **Copy the token immediately** (starts with `ghp_`). You won't see it again.

### Step 2: Create the Secret Gist
1. Go to [gist.github.com](https://gist.github.com).
2. **Description:** "My Strava Calendar".
3. **Filename:** `strava.ics`.
4. **Content:** Type "init" (or anything).
5. Click **Create secret gist** (Green button).
6. Look at the URL of your new Gist: `https://gist.github.com/User/a1b2c3...`
7. Copy the long string of characters at the end. This is your **GIST_ID**.

### Step 3: Update Repository Secrets
Go to this repository's **Settings** > **Secrets and variables** > **Actions** and add two new secrets:

| Secret Name | Value |
| :--- | :--- |
| `GIST_TOKEN` | The `ghp_...` token from Step 1. |
| `GIST_ID` | The ID copied from the URL in Step 2. |

*(Ensure you still have your `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, and `STRAVA_REFRESH_TOKEN` set).*

### Step 4: Make the Repo Private
Now that the `.ics` file is no longer hosted inside this repository:
1. Go to **Settings** > **General**.
2. Scroll to the "Danger Zone".
3. Click **Change repository visibility** -> **Make private**.

---

## 📅 How to Subscribe (New Link)

Your calendar URL has changed. To get the new secure link:

1. Go to your [Gist List](https://gist.github.com).
2. Click on your "My Strava Calendar" gist.
3. Click the **Raw** button.
4. Copy the URL from the browser bar. It will look like this:
   `https://gist.githubusercontent.com/User/raw/long-random-string/strava.ics`
5. Use this URL in Google Calendar or Apple Calendar.