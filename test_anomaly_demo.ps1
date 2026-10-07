$base = "http://localhost:8000"
$email = "anom$(Get-Random)@example.com"
$password = "secret123"

$null = Invoke-RestMethod -Uri "$base/auth/register" -Method Post `
    -Body (@{ email = $email; name = "Anomaly Demo"; phone = "1"; password = $password } | ConvertTo-Json) `
    -ContentType "application/json"
$login = Invoke-RestMethod -Uri "$base/auth/login" -Method Post `
    -Body @{ username = $email; password = $password } `
    -ContentType "application/x-www-form-urlencoded"
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# Grant consents
foreach ($r in @("GPS","LOCATION_HISTORY")) {
    $null = Invoke-RestMethod -Uri "$base/privacy/consents" -Method Post `
        -Body (@{ resource_type = $r; granted = $true } | ConvertTo-Json) `
        -ContentType "application/json" -Headers $headers
}

# Build baseline: 3 short trips, ~5-10 seconds each
Write-Host "Building baseline (3 short trips)..."
for ($i = 1; $i -le 3; $i++) {
    $t = Invoke-RestMethod -Uri "$base/trips" -Method Post -Headers $headers `
        -Body (@{
            route_id = "r1"
            route_name = "Route A"
            origin = "MG Road"
            destination = "Whitefield"
        } | ConvertTo-Json) -ContentType "application/json"
    Start-Sleep -Seconds 5
    $null = Invoke-RestMethod -Uri "$base/trips/$($t.id)/end" -Method Post -Headers $headers
    Write-Host "  baseline trip $i done"
}

# Baseline now has ~5 sec median. Start a long trip.
Write-Host ""
Write-Host "Starting a trip that will run past the baseline threshold..."
$trip = Invoke-RestMethod -Uri "$base/trips" -Method Post -Headers $headers `
    -Body (@{
        route_id = "r1"
        route_name = "Route A"
        origin = "MG Road"
        destination = "Whitefield"
    } | ConvertTo-Json) -ContentType "application/json"

Write-Host "Waiting 15 seconds so elapsed time exceeds baseline * 1.6 + 10..."
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "Triggering anomaly check..."
$resp = Invoke-RestMethod -Uri "$base/trips/$($trip.id)/anomaly/check" -Method Post -Headers $headers
$events = @($resp)
Write-Host "Detected $($events.Count) anomaly event(s):"
$events | ForEach-Object {
    Write-Host ("  type={0} severity={1} score={2}" -f $_.anomaly_type, $_.severity, $_.deviation_score)
    Write-Host ("    {0}" -f $_.description)
}

if ($events.Count -gt 0) {
    $id = $events[0].id
    Write-Host ""
    Write-Host "Responding NEED_HELP to first anomaly..."
    $null = Invoke-RestMethod -Uri "$base/anomaly/$id/respond" -Method Post `
        -Body (@{ response = "NEED_HELP" } | ConvertTo-Json) `
        -ContentType "application/json" -Headers $headers
    Write-Host "State after NEED_HELP:"
    Invoke-RestMethod -Uri "$base/privacy/state" -Method Get -Headers $headers | ConvertTo-Json
}