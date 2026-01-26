# 🏃‍♂️ Strava to Calendar Auto-Sync

Automatically sync your recent Strava activities to a calendar (`.ics`) file using **GitHub Actions**.

Because modern calendar apps (Google Calendar, Apple Calendar) require a stable URL to subscribe to, this tool pushes your calendar data to a pseudo-private **GitHub Secret Gist**. This keeps your main repository private while allowing your calendar app to fetch the data.

---

## 📋 Prerequisites

1.  A free **Strava** account.
2.  A **GitHub** account.
3.  Basic familiarity with the terminal (for one-time setup).

---

## 🚀 Setup Guide

### Phase 1: Strava API Setup
1.  Log in to [Strava API Settings](https://www.strava.com/settings/api).
2.  Create an Application:
    *   **Name:** `Strava2Cal` (or anything you like).
    *   **Website:** `http://localhost`.
    *   **Authorization Callback Domain:** `localhost`.
    *   **Icon:** You **MUST** upload an image/icon, or Strava won't show your keys.
3.  Copy your **Client ID** and **Client Secret**.

### Phase 2: Get your Refresh Token
*This one-time step authorizes the script to access your data forever.*

1.  **Generate the Authorization URL**:
    Replace `[YOUR_CLIENT_ID]` in the URL below with your actual ID, then paste it into your browser:
    ```
    https://www.strava.com/oauth/authorize?client_id=[YOUR_CLIENT_ID]&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all
    ```
2.  **Authorize**: Click "Authorize" on the Strava page. You will be redirected to a broken page (`localhost`).
3.  **Get the Code**: Look at the URL bar of the broken page. Copy the code after `&code=`.
    *   Example: `...&code=a1b2c3d4e5f6...` -> Copy `a1b2c3d4e5f6`.
4.  **Exchange for Refresh Token**:
    Run this command in your terminal (replacing values):
    ```bash
    curl -X POST https://www.strava.com/oauth/token \
      -F client_id=[YOUR_CLIENT_ID] \
      -F client_secret=[YOUR_CLIENT_SECRET] \
      -F code=[CODE_FROM_STEP_3] \
      -F grant_type=authorization_code
    ```
5.  Copy the `"refresh_token"` from the JSON response.

### Phase 3: GitHub Gist Setup (The Storage)
1.  Go to [Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens).
2.  **Generate new token (classic)**:
    *   **Note:** `Strava Gist Sync`
    *   **Expiration:** `No expiration`
    *   **Scopes:** Check **`gist`**.
    *   **Copy the token** (starts with `ghp_`).
3.  Go to [gist.github.com](https://gist.github.com).
    *   **Description:** `My Strava Calendar`
    *   **Filename:** `strava.ics`
    *   **Content:** `init`
    *   **Click:** "Create secret gist".
4.  Copy the **Gist ID** from the URL (the long string at the end of the URL).

### Phase 4: Repository Setup
1.  **Fork** this repository to your account.
2.  Go to **Settings** > **Secrets and variables** > **Actions**.
3.  Add these 5 Repository Secrets:
    *   `STRAVA_CLIENT_ID`
    *   `STRAVA_CLIENT_SECRET`
    *   `STRAVA_REFRESH_TOKEN`
    *   `GIST_TOKEN` (Your `ghp_` token)
    *   `GIST_ID`
4.  Go to the **Actions** tab and enable workflows if prompted.
5.  Select the **Update Strava Calendar** workflow and click **Run workflow**.

---

## � Customization (Optional)

Since you have **forked** the project, you have full control over the code! You can modify `sync_strava.py` to customize your calendar events.

*   **Change Emojis**: Edit the `create_ics_content` function (around line 53) to swap 🏃/🚴 for other symbols.
*   **Filter Activities**: Want to ignore commutes or only sync runs? Add a simple `if` condition in the loop.
*   **Change Descriptions**: Modify what info appears in the calendar event (add heart rate, calories, etc.) by editing the `e.description` field.
*   **Sync ALL History**: By default, only the last 50 activities are synced. To sync EVERYTHING, add a repository secret (or variable) named `SYNC_FULL_HISTORY` with the value `true`.

---

## �📅 How to Subscribe
Once the workflow runs successfully (green checkmark), your Gist will be updated.

1.  Go to your [Gist](https://gist.github.com) and open the `strava.ics` file.
2.  Click the **Raw** button.
3.  Copy the URL.
    *   *Note: To make the link permanent even if you update the Gist, remove the commit hash from the URL.*
    *   Global URL: `https://gist.githubusercontent.com/[USER]/[GIST_ID]/raw/strava.ics`
4.  Paste this URL into your calendar app (Google Calendar: *Add from URL*, Apple Calendar: *New Subscription*).