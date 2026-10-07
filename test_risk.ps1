$base = "http://localhost:8000"
$email = "riskuser$(Get-Random)@example.com"
$password = "secret123"

Write-Host "Registering $email"
$null = Invoke-RestMethod -Uri "$base/auth/register" -Method Post `
    -Body (@{ email = $email; name = "Risk User"; phone = "1"; password = $password } | ConvertTo-Json) `
    -ContentType "application/json"

$login = Invoke-RestMethod -Uri "$base/auth/login" -Method Post `
    -Body @{ username = $email; password = $password } `
    -ContentType "application/x-www-form-urlencoded"

$headers = @{ Authorization = "Bearer $($login.access_token)" }

$context = @{
    hour = 22
    day_of_week = 5
    area_type = "isolated"
    journey_type = "walk"
    incident_density_7d = 8.0
    incident_severity_avg = 3.4
    lighting_score = 0.25
    transit_access = 0.3
    crowd_density = 0.2
    route_length_km = 4.2
    user_baseline_deviation = 0.6
    is_solo = $true
    has_live_share = $false
} | ConvertTo-Json

Write-Host ""
Write-Host "POST /risk/predict"
$result = Invoke-RestMethod -Uri "$base/risk/predict" -Method Post `
    -Body $context -ContentType "application/json" -Headers $headers

$result | ConvertTo-Json -Depth 6