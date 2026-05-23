#!/usr/bin/env bash
# Sign, notarize, staple and re-package the macOS .app produced by PyInstaller.
#
# Required env vars:
#   APPLE_DEVELOPER_ID  e.g. "Developer ID Application: Pierre Scheyer (TEAMID12345)"
#   APPLE_ID            your Apple account email
#   APPLE_PASSWORD      an app-specific password (https://appleid.apple.com -> App-Specific Passwords)
#   APPLE_TEAM_ID       your 10-character team identifier
#
# Run from apps/desktop/ after `pyinstaller --clean ChildShield.spec`.

set -euo pipefail

APP="dist/ChildShield.app"
ENTITLEMENTS="packaging/entitlements.plist"
VERSION="${VERSION:-0.1.0}"
DMG="dist/ChildShield-${VERSION}.dmg"

if [[ ! -d "$APP" ]]; then
  echo "Error: $APP not found. Run pyinstaller first." >&2
  exit 1
fi

: "${APPLE_DEVELOPER_ID:?APPLE_DEVELOPER_ID not set}"
: "${APPLE_ID:?APPLE_ID not set}"
: "${APPLE_PASSWORD:?APPLE_PASSWORD not set}"
: "${APPLE_TEAM_ID:?APPLE_TEAM_ID not set}"

echo "==> Signing $APP …"
codesign --force --deep --options runtime --timestamp \
  --entitlements "$ENTITLEMENTS" \
  --sign "$APPLE_DEVELOPER_ID" \
  "$APP"

echo "==> Verifying signature …"
codesign --verify --deep --strict --verbose=2 "$APP"

echo "==> Submitting for notarization (this can take 1-10 minutes) …"
ZIP="dist/_for_notarization.zip"
ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"
xcrun notarytool submit "$ZIP" \
  --apple-id "$APPLE_ID" \
  --password "$APPLE_PASSWORD" \
  --team-id "$APPLE_TEAM_ID" \
  --wait
rm -f "$ZIP"

echo "==> Stapling notarization ticket …"
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"

echo "==> Re-creating .dmg …"
rm -f "$DMG"
hdiutil create -volname ChildShield \
  -srcfolder "$APP" \
  -ov -format UDZO -fs HFS+ \
  "$DMG"

echo "==> Stapling the .dmg itself (Gatekeeper can verify the dmg) …"
xcrun stapler staple "$DMG"

echo
echo "Done. Signed + notarized + stapled:"
echo "  $APP"
echo "  $DMG"
