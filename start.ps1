#!/usr/bin/env powershell
# Quick Start Script for Multi-Model Chatbot with Google OAuth
# Run this script to start both backend and frontend servers

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Multi-Model Chatbot Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Google OAuth credentials are configured
$envFile = "frontend/multimodel-chatbot/.env.local"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    if ($envContent -like "*GOOGLE_CLIENT_ID=your_google_client_id_here*") {
        Write-Host "⚠️  WARNING: Google OAuth credentials not configured!" -ForegroundColor Yellow
        Write-Host "   Please update frontend/multimodel-chatbot/.env.local with your credentials:" -ForegroundColor Yellow
        Write-Host "   1. Get credentials from: https://console.cloud.google.com/" -ForegroundColor Yellow
        Write-Host "   2. Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET" -ForegroundColor Yellow
        Write-Host "   3. Run this script again" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "⚠️  .env.local not found. Creating from template..." -ForegroundColor Yellow
}

Write-Host "Starting Multi-Model Chatbot..." -ForegroundColor Green
Write-Host ""

# Start Backend
Write-Host "Starting Backend (FastAPI)..." -ForegroundColor Cyan
$backendPath = "cd backend ; python run.py"
Start-Process powershell -ArgumentList "-NoExit -Command $backendPath"
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend (Next.js)..." -ForegroundColor Cyan
$frontendPath = "cd frontend\multimodel-chatbot ; npm run dev"
Start-Process powershell -ArgumentList "-NoExit -Command $frontendPath"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Services Started Successfully!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3002 or 3000" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:3002 in your browser" -ForegroundColor Cyan
Write-Host "2. You should see the Login page with Google button" -ForegroundColor Cyan
Write-Host "3. Click 'Sign in with Google' to authenticate" -ForegroundColor Cyan
Write-Host "4. After login, you'll see the chat interface" -ForegroundColor Cyan
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "- AUTHENTICATION_SETUP.md - Complete authentication guide" -ForegroundColor Yellow
Write-Host "- GOOGLE_AUTH_SETUP.md - Google OAuth credentials setup" -ForegroundColor Yellow
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "- Make sure ports 3000-3002 and 8000 are available" -ForegroundColor Yellow
Write-Host "- Check .env.local has correct Google OAuth credentials" -ForegroundColor Yellow
Write-Host "- Review logs in terminal windows for errors" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop services" -ForegroundColor Yellow
