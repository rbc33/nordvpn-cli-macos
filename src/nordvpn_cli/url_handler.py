"""Register nordvpn:// URL scheme on macOS."""

import shutil
import subprocess
from pathlib import Path

APP_NAME = "NordVPN CLI Handler"
BUNDLE_ID = "com.nordvpn-cli.handler"
APP_PATH = Path.home() / "Applications" / f"{APP_NAME}.app"

PLIST_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" \
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleExecutable</key>
    <string>handler</string>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>NordVPN OAuth Callback</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>nordvpn</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
"""

APPLESCRIPT = '''\
on open location theURL
    set msg to "NordVPN OAuth callback received." & return & return
    set msg to msg & "• CLI — Complete login in Terminal" & return
    set msg to msg & "• Official — Hand off to NordVPN.app" & return
    set msg to msg & "• Uninstall — Remove this handler"
    set dlg to display dialog msg buttons {{"Uninstall", "Official", "CLI"}} default button "CLI"
    set choice to button returned of dlg
    if choice is "CLI" then
        set cmdStr to "{uv_path} run nordvpn login --callback '" & theURL & "'"
        set tmpFile to "/tmp/nordvpn_run.command"
        do shell script "echo " & quoted form of cmdStr & " > " & tmpFile
        do shell script "chmod +x " & tmpFile
        do shell script "open -a Terminal " & quoted form of tmpFile
    else if choice is "Official" then
        do shell script "open -b com.nordvpn.macos " & quoted form of theURL
    else if choice is "Uninstall" then
        set lsreg to "/System/Library/Frameworks/CoreServices.framework"
        set lsreg to lsreg & "/Frameworks/LaunchServices.framework/Support/lsregister"
        do shell script lsreg & " -u \\"{app_path}\\""
        do shell script "rm -rf \\"{app_path}\\""
        display dialog "Handler removed." buttons {{"OK"}} default button "OK"
    end if
end open location
'''


def get_uv_path() -> str:
    """Find uv binary path."""
    result = subprocess.run(["which", "uv"], capture_output=True, text=True, check=False)
    return result.stdout.strip() or "/opt/homebrew/bin/uv"


def install_handler() -> Path:
    """Create and register the URL handler app using osacompile."""
    # Remove old version
    if APP_PATH.exists():
        shutil.rmtree(APP_PATH)

    # Create AppleScript source
    script = APPLESCRIPT.format(uv_path=get_uv_path(), app_path=APP_PATH)
    script_file = Path("/tmp/nordvpn_handler.applescript")
    script_file.write_text(script)

    # Compile to app bundle
    APP_PATH.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["osacompile", "-o", str(APP_PATH), str(script_file)], check=True)
    script_file.unlink()

    # Add URL scheme to Info.plist
    plist_path = APP_PATH / "Contents" / "Info.plist"
    subprocess.run([
        "/usr/libexec/PlistBuddy", "-c",
        "Add :CFBundleIdentifier string " + BUNDLE_ID, str(plist_path)
    ], check=False)
    subprocess.run([
        "/usr/libexec/PlistBuddy", "-c",
        "Add :CFBundleURLTypes array", str(plist_path)
    ], check=False)
    subprocess.run([
        "/usr/libexec/PlistBuddy", "-c",
        "Add :CFBundleURLTypes:0 dict", str(plist_path)
    ], check=False)
    subprocess.run([
        "/usr/libexec/PlistBuddy", "-c",
        "Add :CFBundleURLTypes:0:CFBundleURLSchemes array", str(plist_path)
    ], check=False)
    subprocess.run([
        "/usr/libexec/PlistBuddy", "-c",
        "Add :CFBundleURLTypes:0:CFBundleURLSchemes:0 string nordvpn", str(plist_path)
    ], check=False)

    # Register with Launch Services
    subprocess.run(
        ["/System/Library/Frameworks/CoreServices.framework/Frameworks/"
         "LaunchServices.framework/Support/lsregister", "-R", str(APP_PATH)],
        check=False,
    )
    # Set as default handler for nordvpn:// scheme
    swift = (
        f'import Foundation; import CoreServices; '
        f'LSSetDefaultHandlerForURLScheme("nordvpn" as CFString, "{BUNDLE_ID}" as CFString)'
    )
    subprocess.run(["swift", "-e", swift], check=False, capture_output=True)
    return APP_PATH


def uninstall_handler() -> None:
    """Remove the URL handler app and unregister from Launch Services."""
    if APP_PATH.exists():
        subprocess.run(
            ["/System/Library/Frameworks/CoreServices.framework/Frameworks/"
             "LaunchServices.framework/Support/lsregister", "-u", str(APP_PATH)],
            check=False,
        )
        shutil.rmtree(APP_PATH)
