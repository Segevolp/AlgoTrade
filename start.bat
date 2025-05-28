@echo off

timeout /t 2 >nul

echo Starting frontend...
start cmd /k "cd Front && npm run dev"
