$base = "http://localhost:8000"
$email = "trip$(Get-Random)@example.com"
$password = "secret123"

function Section($msg) {
    Write-Host ""
    Write-Host "=== $msg ===" -ForegroundColor Cyan
}

Section "Register / Login"
$null = Invoke-RestMethod -Uri "$base/auth/register" -Method Post `
    -Body (@{ email = $email; name = "Trip Tester"; phone = "1"; password = $password } | ConvertTo-Json) `
    -ContentType "application/json"
$login = Invoke-RestMethod -Uri "$base/auth/login" -Method Post `
    -Body @{ username = $email; password = $password } `
    -ContentType "application/x-www-form-urlencoded"
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Write-Host "Logged in as $email"

Section "1. Consents (default state)"
$consents = Invoke-RestMethod -Uri "$base/privacy/consents" -Method Get -Headers $headers
$consents | ForEach-Object { Write-Host ("  {0,-20} granted={1}" -f $_.resource_type, $_.granted) }

Section "2. Grant GPS + LOCATION_HISTORY consent"
foreach ($r in @("GPS","LOCATION_HISTORY")) {
    $body = @{ resource_type = $r; granted = $true } | ConvertTo-Json
    $null = Invoke-RestMethod -Uri "$base/privacy/consents" -Method Post `
        -Body $body -ContentType "application/json" -Headers $headers
}
Write-Host "Granted."

Section "3. Privacy state (should be IDLE)"
Invoke-RestMethod -Uri "$base/privacy/state" -Method Get -Headers $headers | ConvertTo-Json

Section "4. Start Safety Trip"
$trip = Invoke-RestMethod -Uri "$base/trips" -Method Post -Headers $headers `
    -Body (@{
        route_id = "r1"
        route_name = "Route A - Main Road"
        origin = "MG Road"
        destination = "Whitefield"
    } | ConvertTo-Json) -ContentType "application/json"
$tripId = $trip.id
Write-Host "Trip ID: $tripId  state: $($trip.privacy_state)"

Section "5. Privacy state (should be TRIP_ACTIVE)"
Invoke-RestMethod -Uri "$base/privacy/state" -Method Get -Headers $headers | ConvertTo-Json

Section "6. Add 3 locations (consent granted)"
$coords = @(
    @{ latitude = 12.9716; longitude = 77.5946 },
    @{ latitude = 12.9720; longitude = 77.5950 },
    @{ latitude = 12.9724; longitude = 77.5954 }
)
foreach ($c in $coords) {
    $body = @{ latitude = $c.latitude; longitude = $c.longitude; accuracy_m = 8; source = "mock" } | ConvertTo-Json
    $null = Invoke-RestMethod -Uri "$base/trips/$tripId/locations" -Method Post `
        -Body $body -ContentType "application/json" -Headers $headers
    Write-Host "  location added: $($c.latitude),$($c.longitude)"
}

Section "7. Revoke GPS consent"
$null = Invoke-RestMethod -Uri "$base/privacy/consents" -Method Post `
    -Body (@{ resource_type = "GPS"; granted = $false } | ConvertTo-Json) `
    -ContentType "application/json" -Headers $headers
Write-Host "GPS consent revoked."

Section "8. Try to add a location again (should be 403)"
try {
    $body = @{ latitude = 12.9800; longitude = 77.6000 } | ConvertTo-Json
    $null = Invoke-RestMethod -Uri "$base/trips/$tripId/locations" -Method Post `
        -Body $body -ContentType "application/json" -Headers $headers -ErrorAction Stop
    Write-Host "UNEXPECTED: allowed" -ForegroundColor Red
} catch {
    Write-Host "Correctly rejected: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Green
}

Section "9. Re-grant GPS consent"
$null = Invoke-RestMethod -Uri "$base/privacy/consents" -Method Post `
    -Body (@{ resource_type = "GPS"; granted = $true } | ConvertTo-Json) `
    -ContentType "application/json" -Headers $headers
Write-Host "GPS consent re-granted."

Section "10. Trigger anomaly check"
$response = Invoke-RestMethod -Uri "$base/trips/$tripId/anomaly/check" -Method Post -Headers $headers
$anomalies = @($response)
if ($anomalies.Count -gt 0) {
    $anomalies | ForEach-Object {
        Write-Host "  anomaly: $($_.anomaly_type) severity=$($_.severity) score=$($_.deviation_score)"
    }
    $firstAnomalyId = $anomalies[0].id

    Section "11. Respond SAFE to first anomaly"
    $null = Invoke-RestMethod -Uri "$base/anomaly/$firstAnomalyId/respond" -Method Post `
        -Body (@{ response = "SAFE" } | ConvertTo-Json) `
        -ContentType "application/json" -Headers $headers
    Write-Host "Responded SAFE."
} else {
    Write-Host "No anomalies detected. This is fine; depends on baseline and timing."
}

Section "12. End trip"
$ended = Invoke-RestMethod -Uri "$base/trips/$tripId/end" -Method Post -Headers $headers
Write-Host "Trip ended. status=$($ended.status) state=$($ended.privacy_state)"

Section "13. Privacy state (should be RESOLVED)"
Invoke-RestMethod -Uri "$base/privacy/state" -Method Get -Headers $headers | ConvertTo-Json

Section "14. Privacy Receipt for this trip"
$receipt = Invoke-RestMethod -Uri "$base/privacy/receipt/$tripId" -Method Get -Headers $headers
$receipt | ConvertTo-Json -Depth 4

Section "15. Audit log (last 20 entries)"
$log = Invoke-RestMethod -Uri "$base/privacy/audit-log" -Method Get -Headers $headers
$log | Select-Object -First 20 | ForEach-Object {
    Write-Host ("  [{0}] {1,-10} {2,-18} {3}" -f $_.privacy_state, $_.resource_type, $_.action, $_.status)
}

Section "16. Trip history"
Invoke-RestMethod -Uri "$base/trips/history" -Method Get -Headers $headers | ConvertTo-Json -Depth 3

Write-Host ""
Write-Host "=== PHASE 4 TEST COMPLETE ===" -ForegroundColor Green