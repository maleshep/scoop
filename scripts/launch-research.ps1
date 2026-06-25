# Launch Chrome with the research profile (Slot4) on DevTools port 5192
# Run this script whenever you want to sync LinkedIn saved posts

$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$userDataDir = "C:\Users\M316235\AppData\Local\Google\Chrome\Slot4"
$port = 5192

Write-Host "Launching Chrome Research (Slot4, port $port)..."

$proc = Start-Process -FilePath $chrome -ArgumentList @(
    "--remote-debugging-port=$port",
    "--remote-debugging-address=127.0.0.1",
    "--user-data-dir=`"$userDataDir`"",
    "--profile-directory=Default",
    "--no-first-run",
    "--no-default-browser-check",
    "https://www.linkedin.com/my-items/saved-posts/?savedPostType=ALL"
) -PassThru

Write-Host "Chrome started: PID $($proc.Id)"
Write-Host "DevTools port: $port"
Write-Host ""
Write-Host "If this is your first time, sign into LinkedIn in the Chrome window."
Write-Host "After signing in, your session will persist in Slot4 for future use."
Write-Host ""
Write-Host "Once LinkedIn shows your saved posts, tell the agent: 'sync my saved articles'"
