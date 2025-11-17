# Batch processing script for sermon transcription
$env:GOOGLE_APPLICATION_CREDENTIALS = "google-credentials.json"
$env:GOOGLE_CLOUD_BUCKET = "sermons-transcription-temp"

Write-Host "Starting batch processing of 658 videos..."
Write-Host "This will take approximately 4-5 hours"
Write-Host "Progress will be logged to batch_log.txt"
Write-Host ""

python scripts/fetch_batch.py --ids-file videos_to_reprocess.txt --max-videos 658 --reprocess 2>&1 | Tee-Object -FilePath batch_log.txt

Write-Host ""
Write-Host "Batch processing complete!"
