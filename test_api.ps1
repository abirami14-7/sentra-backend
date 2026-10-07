$base = "http://localhost:8000"
$email = "aarohi$(Get-Random)@example.com"
$password = "secret123"

Write-Host ""
Write-Host "=== 1. Health check ===" -ForegroundColor Cyan
$r = Invoke-RestMethod -Uri "$base/health" -Method Get
$r | ConvertTo-Json

Write-Host ""
Write-Host "=== 2. Register ($email) ===" -ForegroundColor Cyan
$registerBody = @{
    email    = $email
    name     = "Aarohi Sharma"
    phone    = "+91 90000 00000"
    password = $password
} | ConvertTo-Json

$register = Invoke-RestMethod -Uri "$base/auth/register" -Method Post `
    -Body $registerBody -ContentType "application/json"
$register | ConvertTo-Json

Write-Host ""
Write-Host "=== 3. Login ===" -ForegroundColor Cyan
$login = Invoke-RestMethod -Uri "$base/auth/login" -Method Post `
    -Body @{ username = $email; password = $password } `
    -ContentType "application/x-www-form-urlencoded"
$token = $login.access_token
Write-Host "Token (first 30 chars): $($token.Substring(0,30))..."

$headers = @{ Authorization = "Bearer $token" }

Write-Host ""
Write-Host "=== 4. GET /users/me (protected) ===" -ForegroundColor Cyan
$me = Invoke-RestMethod -Uri "$base/users/me" -Method Get -Headers $headers
$me | ConvertTo-Json -Depth 5

Write-Host ""
Write-Host "=== 5. POST /users/me/emergency-contacts ===" -ForegroundColor Cyan
$contactBody = @{
    name         = "Riya Sharma"
    phone        = "+91 90000 11111"
    relationship = "Sister"
    priority     = 1
} | ConvertTo-Json

$contact = Invoke-RestMethod -Uri "$base/users/me/emergency-contacts" `
    -Method Post -Body $contactBody -ContentType "application/json" -Headers $headers
$contact | ConvertTo-Json

Write-Host ""
Write-Host "=== 6. GET /users/me again (contact should appear) ===" -ForegroundColor Cyan
$me2 = Invoke-RestMethod -Uri "$base/users/me" -Method Get -Headers $headers
$me2 | ConvertTo-Json -Depth 5

Write-Host ""
Write-Host "=== 7. GET /users/me without token (should be 401) ===" -ForegroundColor Cyan
try {
    Invoke-RestMethod -Uri "$base/users/me" -Method Get -ErrorAction Stop
    Write-Host "UNEXPECTED: call succeeded" -ForegroundColor Red
} catch {
    Write-Host "Correctly rejected with status $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== ALL CHECKS DONE ===" -ForegroundColor Green