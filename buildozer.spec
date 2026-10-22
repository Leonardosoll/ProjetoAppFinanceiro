[app]

# (str) Title of your application
title = Conciliador Financeiro

# (str) Package name
package.name = conciliadorapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.financeiro.conciliador

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 2.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy,kivymd,pdfplumber,pypdf
requirements = python3,kivy,kivymd,pdfplumber,pypdf

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK version
android.ndk = 25b

# (bool) If True, then skip try to update the Android sdk
android.skip_update = False

# (bool) If True, then accept all SDK licenses
android.accept_sdk_licenses = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = error, 1 = warning)
warn_on_root = 1
