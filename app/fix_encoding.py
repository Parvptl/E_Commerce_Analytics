#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Encoding Fix Script for NEXUS Dashboard
Works on Windows without emoji in source code
"""

import os
import sys
from pathlib import Path

def fix_file_encoding(file_path):
    """Fix encoding issues in a single file using byte patterns"""
    try:
        # Read file as binary
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        
        # Decode with latin-1 (safe fallback that never fails)
        content = content_bytes.decode('latin-1')
        
        # Fix common corrupted emoji patterns
        # These are the byte sequences that appear as white boxes
        replacements = {
            # Chart/Graph emojis
            '\xf0\x9f\x93\x88': '📈',  # Chart increasing
            '\xf0\x9f\x93\x8a': '📊',  # Bar chart
            'ðŸ"ˆ': '📈',
            'ðŸ"Š': '📊',
            
            # Analysis emojis
            '\xf0\x9f\x94\xac': '🔬',  # Microscope
            'ðŸ"¬': '🔬',
            
            # Shopping/Business
            '\xf0\x9f\x9b\x92': '🛒',  # Shopping cart
            'ðŸ›'': '🛒',
            
            # Target/Goals
            '\xf0\x9f\x8e\xaf': '🎯',  # Target
            'ðŸŽ¯': '🎯',
            
            # Network/Globe
            '\xf0\x9f\x8c\x90': '🌐',  # Globe
            'ðŸŒ': '🌐',
            
            # Home
            '\xf0\x9f\x8f\xa0': '🏠',  # Home
            'ðŸ ': '🏠',
            
            # Status symbols
            '\xe2\x9c\x85': '✅',  # Check mark
            'âœ…': '✅',
            '\xe2\x9c\x82': '✂',  # Scissors
            'âœ‚ï¸': '✂️',
            '\xe2\x9d\x8c': '❌',  # X mark
            'âŒ': '❌',
            '\xe2\x9a\xa0': '⚠',  # Warning
            'âš ï¸': '⚠️',
            
            # Arrow
            '\xe2\x86\x92': '→',  # Right arrow
            'â†'': '→',
            '\xe2\x9e\xa1': '➡',  # Right arrow
            'âž¡ï¸': '➡️',
            
            # Currency
            '\xe2\x82\xb9': '₹',  # Rupee
            'â‚¹': '₹',
            
            # More emojis
            '\xf0\x9f\x94\x8d': '🔍',  # Magnifying glass
            'ðŸ"': '🔍',
            '\xf0\x9f\x93\x8b': '📋',  # Clipboard
            'ðŸ"': '📋',
            '\xf0\x9f\x93\x89': '📉',  # Chart decreasing
            'ðŸ"‰': '📉',
            '\xf0\x9f\x93\x84': '📄',  # Page
            'ðŸ"„': '📄',
            '\xf0\x9f\x93\xa5': '📥',  # Inbox
            'ðŸ"¥': '📥',
            '\xf0\x9f\x93\xa4': '📤',  # Outbox
            'ðŸ"¤': '📤',
            '\xf0\x9f\x92\xa1': '💡',  # Light bulb
            'ðŸ'¡': '💡',
            '\xf0\x9f\x94\x97': '🔗',  # Link
            'ðŸ"': '🔗',
            '\xf0\x9f\x8e\xa8': '🎨',  # Artist palette
            'ðŸŽ¨': '🎨',
            '\xf0\x9f\x92\xaa': '💪',  # Flexed bicep
            'ðŸ'ª': '💪',
            '\xf0\x9f\x94\xa5': '🔥',  # Fire
            'ðŸ"¥': '🔥',
            '\xf0\x9f\x93\x8c': '📌',  # Pushpin
            'ðŸ"Œ': '📌',
            '\xf0\x9f\x94\xb4': '🔴',  # Red circle
            'ðŸ"´': '🔴',
            '\xf0\x9f\x9f\xa1': '🟡',  # Yellow circle
            'ðŸŸ¡': '🟡',
            '\xf0\x9f\x9f\xa2': '🟢',  # Green circle
            'ðŸŸ¢': '🟢',
            '\xf0\x9f\xa7\xad': '🧭',  # Compass
            'ðŸ§­': '🧭',
            '\xf0\x9f\x91\x8b': '👋',  # Waving hand
            'ðŸ'‹': '👋',
            '\xf0\x9f\x93\x82': '📂',  # Folder
            'ðŸ"‚': '📂',
            '\xf0\x9f\x8c\xb3': '🌳',  # Tree
            'ðŸŒ³': '🌳',
            '\xf0\x9f\x94\xb5': '🔵',  # Blue circle
            'ðŸ"µ': '🔵',
            '\xf0\x9f\xa7\xaa': '🧪',  # Test tube
            'ðŸ§ª': '🧪',
            '\xf0\x9f\x93\x96': '📖',  # Book
            'ðŸ"–': '📖',
        }
        
        # Apply replacements
        original_content = content
        for broken, fixed in replacements.items():
            content = content.replace(broken, fixed)
        
        # Write back with UTF-8 if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            return True, "Fixed"
        else:
            return True, "No changes"
            
    except Exception as e:
        return False, str(e)

def main():
    """Fix encoding in all Python files"""
    print("=" * 70)
    print("NEXUS Dashboard - Encoding Fix Script (Windows Compatible)")
    print("=" * 70)
    print()
    
    # Get project root (parent of current directory)
    script_dir = Path(__file__).parent
    
    # If script is in app/ directory, go up one level
    if script_dir.name == 'app':
        root_dir = script_dir.parent
    else:
        root_dir = script_dir
    
    print(f"Scanning directory: {root_dir}")
    print()
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments and cache
        dirs[:] = [d for d in dirs if d not in ['venv', 'env', '.venv', '__pycache__', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    print(f"Found {len(python_files)} Python files")
    print()
    
    # Fix each file
    fixed_count = 0
    unchanged_count = 0
    error_count = 0
    
    for file_path in python_files:
        success, message = fix_file_encoding(file_path)
        
        relative_path = file_path.relative_to(root_dir)
        
        if success:
            if message == "Fixed":
                print(f"[FIXED] {relative_path}")
                fixed_count += 1
            else:
                print(f"[OK] {relative_path}")
                unchanged_count += 1
        else:
            print(f"[ERROR] {relative_path}: {message}")
            error_count += 1
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files:     {len(python_files)}")
    print(f"Fixed:           {fixed_count}")
    print(f"Unchanged:       {unchanged_count}")
    print(f"Errors:          {error_count}")
    print("=" * 70)
    print()
    
    if fixed_count > 0:
        print("SUCCESS! Files have been fixed.")
        print()
        print("Next steps:")
        print("1. Restart your Streamlit app")
        print("2. Clear browser cache (Ctrl+Shift+R)")
        print("3. Check if emojis display correctly")
    else:
        print("No files needed fixing. If you still see white boxes:")
        print("1. Try restarting Streamlit")
        print("2. Clear browser cache (Ctrl+Shift+R)")
        print("3. Check VS Code encoding settings (bottom-right corner)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        sys.exit(1)