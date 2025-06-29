#!/bin/bash
# Quick conversation capture script for hotkey activation
LOG_DIR="/Users/mikaeleage/Research & Analytics Services/001/logs/user_logs_capture_recovery"
TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")

# Create capture file
CAPTURE_FILE="$LOG_DIR/hotkey_capture_$TIMESTAMP.md"

echo "🔥 HOTKEY CONVERSATION CAPTURE - $TIMESTAMP" > "$CAPTURE_FILE"
echo "=============================================" >> "$CAPTURE_FILE"
echo "" >> "$CAPTURE_FILE"

# Capture current iTerm2 session
osascript << EOF >> "$CAPTURE_FILE"
tell application "iTerm2"
    tell current window
        tell current session
            get contents
        end tell
    end tell
end tell
EOF

echo "" >> "$CAPTURE_FILE"
echo "✅ Captured: $CAPTURE_FILE"
echo "📋 Copied to clipboard!"

# Copy file path to clipboard for easy access
echo "$CAPTURE_FILE" | pbcopy

# Show notification
osascript -e 'display notification "Conversation captured!" with title "Claude Code Logger"'