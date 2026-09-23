@echo off
title SUVI Android Mobile Application Setup & Build
color 0a

echo =======================================================================
echo          SUVI Android Mobile Application Builder & Deployment
echo =======================================================================
echo.

cd /d "%~dp0\..\android_app"

echo Available Deployment Methods for SUVI Android App:
echo.
echo [1] PWA Mobile App (Instant Install in 10 seconds - Recommended):
echo     1. Make sure SUVI server is running (double click start_suvi.bat)
echo     2. Connect your phone to the same Wi-Fi as your PC
echo     3. Open Google Chrome on your Android phone
echo     4. Go to: http://[YOUR-PC-IP]:8000
echo     5. Tap the prompt '📲 INSTALL APP' or tap Chrome Menu (3 dots) -> 'Install app'
echo     6. SUVI is now installed on your Android home screen as a full app!
echo.
echo [2] Build Native APK in Android Studio:
echo     1. Open Android Studio
echo     2. Click 'Open Existing Project'
echo     3. Select folder: %CD%
echo     4. Click Build -> Build Bundle(s) / APK(s) -> Build APK(s)
echo     5. Transfer output APK to your phone or install directly via ADB!
echo.
echo =======================================================================
echo.

pause
