#!/usr/bin/env python3
"""
Automated Tesseract OCR Installer
Run this script to automatically download and install Tesseract OCR
"""

import os
import sys
import subprocess
import urllib.request
import tempfile
import shutil

def download_file(url, destination):
    """Download a file from URL to destination."""
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"✓ Downloaded to {destination}")
        return True
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return False

def install_tesseract():
    """Attempt to install Tesseract OCR."""
    print("=" * 70)
    print("TESSERACT OCR AUTOMATIC INSTALLER")
    print("=" * 70)
    print()
    
    # Check if already installed
    print("[1] Checking if Tesseract is already installed...")
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            print("✓ Tesseract is already installed!")
            print(result.stdout)
            return True
    except:
        pass
    
    print("✗ Tesseract not found in PATH")
    print()
    
    # Try Chocolatey first
    print("[2] Attempting installation via Chocolatey...")
    try:
        result = subprocess.run(['choco', '--version'], 
                              capture_output=True,
                              timeout=5)
        if result.returncode == 0:
            print("✓ Chocolatey found, installing Tesseract...")
            subprocess.run(['choco', 'install', 'tesseract', '-y'],
                         capture_output=False)
            
            # Verify
            result = subprocess.run(['tesseract', '--version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            if result.returncode == 0:
                print("✓ Tesseract installed successfully!")
                return True
    except:
        pass
    
    print("⚠ Chocolatey not available or installation failed")
    print()
    
    # Manual download option
    print("[3] Manual Installation Required")
    print()
    print("Since automated installation requires admin privileges,")
    print("please follow these steps to install manually:")
    print()
    print("1. Open this link in your browser:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("2. Download the latest Windows installer:")
    print("   tesseract-ocr-w64-setup-v5.x.x.exe")
    print()
    print("3. Run the installer with Administrator privileges:")
    print("   - Right-click the .exe file")
    print("   - Select 'Run as Administrator'")
    print()
    print("4. Accept the license and use default installation path:")
    print("   C:\\Program Files\\Tesseract-OCR")
    print()
    print("5. Complete the installation")
    print()
    print("6. Restart PowerShell/Command Prompt and run:")
    print("   tesseract --version")
    print()
    print("7. Your app will automatically detect Tesseract!")
    print()
    print("=" * 70)
    
    return False

if __name__ == "__main__":
    try:
        success = install_tesseract()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
