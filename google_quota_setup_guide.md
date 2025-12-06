# Google Maps API Quota Setup Guide

## What Google is Asking For

Google cannot proceed with your billing adjustment request until you:
1. **Set up proper quota limits** on your API key
2. **Configure quotas** to prevent future unexpected charges
3. **Notify them** once you've completed the setup

## Understanding the Free Tiers

Google is telling you about free monthly limits:
- **Routes: Compute Route Matrix Pro**: 5,000 free requests/month
- **Routes: Compute Route Matrix Essentials**: 10,000 free requests/month

You're using the endpoint: `https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix`

This endpoint can be either Pro or Essentials depending on the features you use. Check your Google Cloud Console billing to see which one you're being charged for.

## Steps to Set Up Quotas

**IMPORTANT:** Quotas are NOT set on the API key page. They're set at the API level for your entire project.

### 1. Set Up Quotas for Routes API

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Navigate to: **APIs & Services** → **Dashboard**
3. In the search box at the top, type "Routes API" and select it
4. Click on the **Quotas** tab (at the top of the page)
5. Look for quota metrics like:
   - "Routes: Compute Route Matrix Pro - Requests per day"
   - "Routes: Compute Route Matrix Essentials - Requests per day"
   - Or monthly quotas
6. Click on the quota you want to limit (e.g., "Requests per day")
7. Click **Edit Quotas** button
8. Set a custom limit (e.g., 200 requests/day to stay under 5,000-10,000/month)
9. Click **Save**

### 2. Set Up Quotas for Geocoding API

1. Still in **APIs & Services** → **Dashboard**
2. Search for "Geocoding API" and select it
3. Click on the **Quotas** tab
4. Find quota metrics like:
   - "Geocoding API - Requests per day"
   - "Geocoding API - Requests per month"
5. Click on the quota and click **Edit Quotas**
6. Set a custom limit (e.g., 1,000 requests/day or 35,000/month)
7. Click **Save**

**Note:** 
- Some projects don't allow editing quotas directly (especially for free tier limits)
- If you don't see an "Edit Quotas" button, that's okay - **billing alerts are the most important thing to set up**
- Google may be satisfied with just billing alerts and API key restrictions
- You can still reply to Google saying you've set up billing alerts and restricted the API key

### 3. Recommended Quota Settings

To stay within free tier and prevent unexpected charges:

**For Routes API:**
- Set daily quota to: **~200 requests/day** (stays under 5,000-10,000/month)
- Or set monthly quota to: **4,000 requests/month** (leaves buffer under free tier)

**For Geocoding API:**
- Check free tier limit (usually 40,000/month)
- Set daily quota to: **~1,000 requests/day** or monthly to **35,000/month**

### 4. Enable Billing Alerts (IMPORTANT - Do This Even If Quotas Don't Work)

If you can't set quotas (some projects don't allow quota editing), set up billing alerts instead:

1. Go to **Billing** → **Budgets & alerts**
2. Click **Create Budget**
3. Select **Google Maps Platform** as the service
4. Set budget amount (e.g., $5 or $10)
5. Set alert threshold (e.g., 50% and 90% of budget)
6. Add your email to receive alerts

### 5. Restrict API Key (You Can Do This Now)

You're already on the API key page, so you can do this:

1. In the **API restrictions** section (which you can see)
2. Make sure **"Restrict key"** is selected (it looks like it already is)
3. Make sure only **Routes API** and **Geocoding API** are selected
4. Click **Save** at the bottom

This prevents accidental use of other paid APIs.

## How to Check Which Version You're Using

1. Go to **Billing** → **Reports**
2. Filter by **Google Maps Platform**
3. Look for line items showing:
   - "Routes: Compute Route Matrix Pro" (5,000 free/month)
   - "Routes: Compute Route Matrix Essentials" (10,000 free/month)

## Response to Google

Once you've set up the quotas, reply to Joana with:

```
Hello Joana,

Thank you for the information. I have now set up proper quota limits on my API key:

- Routes API: Set daily quota to [X] requests/day (or monthly quota to [Y] requests/month)
- Geocoding API: Set daily quota to [X] requests/day (or monthly quota to [Y] requests/month)
- Enabled billing alerts in Google Cloud Console
- Restricted API key to only Routes API and Geocoding API

I've configured the quotas to stay within the free tier limits to prevent future unexpected charges.

Please let me know if you need any additional information or if you can now proceed with reviewing my billing adjustment request.

Thank you,
[Your Name]
```

## Quick Checklist

- [ ] Logged into Google Cloud Console
- [ ] Found my API key
- [ ] Set quota limits for Routes API
- [ ] Set quota limits for Geocoding API
- [ ] Enabled billing alerts
- [ ] Restricted API key to only necessary APIs
- [ ] Replied to Google confirming setup is complete

