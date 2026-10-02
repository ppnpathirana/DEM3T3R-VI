@echo off
echo ========================================================
echo   CropGuard AI - Android App & APK Build Engine
echo ========================================================
echo.
echo [1/3] Compiling optimized React Vite production assets...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Vite build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Syncing assets to native Android Gradle project...
call npx cap sync android
if %errorlevel% neq 0 (
    echo [ERROR] Capacitor sync failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Checking for Gradle / Android toolchain...
if exist "android\gradlew.bat" (
    cd android
    echo Attempting native APK compilation with Gradle wrapper...
    call gradlew.bat assembleDebug
    cd ..
    if exist "android\app\build\outputs\apk\debug\app-debug.apk" (
        echo.
        echo ========================================================
        echo [SUCCESS] APK compiled successfully!
        echo Location: android\app\build\outputs\apk\debug\app-debug.apk
        echo ========================================================
        pause
        exit /b 0
    )
)

echo.
echo ========================================================
echo Opening Android project in Android Studio...
echo (In Android Studio, click: Build -^> Build Bundle(s) / APK(s) -^> Build APK)
echo ========================================================
call npx cap open android
pause
