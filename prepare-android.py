#!/usr/bin/env python3
"""Allow the installed OpenJDK 6 while retaining KitKat's Java 6 version checks."""
from pathlib import Path
root = Path(__file__).resolve().parent
path = root / 'aosp/build/core/main.mk'
text = path.read_text()
start_marker = '# Check for the corrent jdk\n'
end_marker = '# Check for the correct version of java\n'
replacement = '# OpenJDK 6 bring-up: keep the upstream java/javac 1.6 checks below.\n'
if start_marker in text:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    text = text[:start] + replacement + text[end:]
    path.write_text(text)
assert "java_version :=" in text and "javac_version :=" in text
print('Prepared experimental OpenJDK 6 build compatibility; version checks retained.')
