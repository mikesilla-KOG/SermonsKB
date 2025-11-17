# Google Cloud Speech-to-Text Setup Guide

## 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable billing (required for Speech-to-Text API)
   - New users get $300 free credits for 90 days
   - Speech-to-Text pricing: ~$0.006/minute for standard recognition

## 2. Enable Speech-to-Text API

1. Go to https://console.cloud.google.com/apis/library/speech.googleapis.com
2. Click "Enable" button
3. Wait for activation

## 3. Create Service Account & Download Credentials

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. Name it "sermonsKB-transcription"
4. Click "Create and Continue"
5. Grant role: **"Cloud Speech Client"**
6. Click "Done"
7. Click on the service account email
8. Go to "Keys" tab
9. Click "Add Key" → "Create new key"
10. Choose "JSON" format
11. Download the JSON file

## 4. Create Cloud Storage Bucket (for audio files > 10MB)

1. Go to https://console.cloud.google.com/storage/browser
2. Click "Create Bucket"
3. Name it: `sermons-transcription-temp` (must be globally unique, try adding random numbers if taken)
4. Location: Choose "Region" and select closest to you (e.g., `us-central1`)
5. Storage class: "Standard"
6. Access control: "Uniform"
7. Click "Create"

## 5. Set Up Locally

1. Save the JSON file to: `C:\Users\mikes\SermonsKB\google-credentials.json`
2. Add to .env file:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=google-credentials.json
   GOOGLE_CLOUD_BUCKET=sermons-transcription-temp
   LOCAL_WHISPER_MODEL=
   ```

## 6. Install Python Package

The package will be installed automatically when you run the updated script.

## 7. Pricing Estimate

- 658 videos remaining
- Average ~20 minutes per sermon = 13,160 minutes total
- Cost: 13,160 × $0.006 = ~$79 (well within $300 free credit)
- Processing time: ~1-2 seconds per minute = ~4-5 hours total

Much faster than Whisper and uses free credits!
