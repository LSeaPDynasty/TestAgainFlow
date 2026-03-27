"""
ADB utility functions - Android Debug Bridge wrapper
"""
import subprocess
import json
from typing import List, Dict, Optional, Any
from app.config import settings


def run_adb_command(args: List[str], device_serial: Optional[str] = None) -> str:
    """
    Run ADB command and return output

    Args:
        args: ADB command arguments (without 'adb' prefix)
        device_serial: Device serial number (for specific device commands)

    Returns:
        Command output as string
    """
    cmd = [settings.adb_path]

    if device_serial:
        cmd.extend(["-s", device_serial])

    cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        raise Exception(f"ADB command timeout: {' '.join(cmd)}")
    except Exception as e:
        raise Exception(f"ADB command failed: {str(e)}")


def get_adb_devices() -> List[Dict[str, Any]]:
    """
    Get list of ADB devices

    Returns:
        List of device info dicts with 'serial' and 'model' keys
    """
    try:
        output = run_adb_command(["devices", "-l"])
        devices = []

        for line in output.strip().split('\n'):
            if not line or line.startswith('List of devices'):
                continue

            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]

                if status == 'device':
                    device_info = {'serial': serial, 'status': status}

                    # Parse additional info
                    for part in parts[2:]:
                        if ':' in part:
                            key, value = part.split(':', 1)
                            device_info[key] = value

                    devices.append(device_info)

        return devices
    except Exception as e:
        raise Exception(f"Failed to get ADB devices: {str(e)}")


def check_device_online(device_serial: str) -> bool:
    """
    Check if device is online

    Args:
        device_serial: Device serial number

    Returns:
        True if device is online, False otherwise
    """
    try:
        devices = get_adb_devices()
        for device in devices:
            if device.get('serial') == device_serial and device.get('status') == 'device':
                return True
        return False
    except Exception:
        return False


def get_device_property(device_serial: str, prop_name: str) -> Optional[str]:
    """
    Get device property

    Args:
        device_serial: Device serial number
        prop_name: Property name (e.g., 'ro.product.model', 'ro.build.version.release')

    Returns:
        Property value or None
    """
    try:
        output = run_adb_command(["shell", "getprop", prop_name], device_serial=device_serial)
        return output.strip() or None
    except Exception:
        return None


def get_device_info(device_serial: str) -> Dict[str, Any]:
    """
    Get complete device information

    Args:
        device_serial: Device serial number

    Returns:
        Device info dict
    """
    info = {
        'serial': device_serial,
        'model': get_device_property(device_serial, 'ro.product.model'),
        'os_version': get_device_property(device_serial, 'ro.build.version.release'),
        'android_version': get_device_property(device_serial, 'ro.build.version.release'),
        'brand': get_device_property(device_serial, 'ro.product.brand'),
        'manufacturer': get_device_property(device_serial, 'ro.product.manufacturer'),
        'device': get_device_property(device_serial, 'ro.product.device'),
    }

    # Remove None values
    return {k: v for k, v in info.items() if v is not None}


def find_element(device_serial: str, locator_type: str, locator_value: str) -> Dict[str, Any]:
    """
    Find element on device using UIAutomator

    Args:
        device_serial: Device serial number
        locator_type: Locator type (resource-id, text, xpath, etc.)
        locator_value: Locator value

    Returns:
        Dict with 'found' bool and 'bounds' if found
    """
    # TODO: Implement actual element finding using UIAutomator or Appium
    # For now, return mock response
    return {
        'found': False,
        'locator_type': locator_type,
        'locator_value': locator_value,
        'bounds': None
    }


def tap_element(device_serial: str, x: int, y: int) -> bool:
    """
    Tap element at coordinates

    Args:
        device_serial: Device serial number
        x: X coordinate
        y: Y coordinate

    Returns:
        True if successful
    """
    try:
        run_adb_command(["shell", "input", "tap", str(x), str(y)], device_serial=device_serial)
        return True
    except Exception:
        return False


def input_text(device_serial: str, text: str) -> bool:
    """
    Input text into focused field

    Args:
        device_serial: Device serial number
        text: Text to input

    Returns:
        True if successful
    """
    try:
        # Convert unicode to \u escape sequences
        escaped_text = text.encode('unicode_escape').decode('ascii').replace('\\', '\\\\')
        run_adb_command(["shell", "input", "text", text], device_serial=device_serial)
        return True
    except Exception:
        return False


def press_back(device_serial: str) -> bool:
    """
    Press back button

    Args:
        device_serial: Device serial number

    Returns:
        True if successful
    """
    try:
        run_adb_command(["shell", "input", "keyevent", "4"], device_serial=device_serial)
        return True
    except Exception:
        return False


def take_screenshot(device_serial: str, local_path: str) -> bool:
    """
    Take device screenshot

    Args:
        device_serial: Device serial number
        local_path: Local file path to save screenshot

    Returns:
        True if successful
    """
    try:
        # Capture screenshot to device
        run_adb_command(["shell", "screencap", "-p", "/sdcard/screenshot.png"], device_serial=device_serial)

        # Pull to local
        run_adb_command(["pull", "/sdcard/screenshot.png", local_path], device_serial=device_serial)

        # Clean up device file
        run_adb_command(["shell", "rm", "/sdcard/screenshot.png"], device_serial=device_serial)

        return True
    except Exception:
        return False


def start_activity(device_serial: str, activity: str) -> bool:
    """
    Start Android activity

    Args:
        device_serial: Device serial number
        activity: Activity name (e.g., com.example.app.MainActivity)

    Returns:
        True if successful
    """
    try:
        # Parse package and activity
        parts = activity.split('/')
        if len(parts) == 2:
            package, activity_name = parts
            run_adb_command([
                "shell", "am", "start",
                "-n", f"{package}/{activity_name}"
            ], device_serial=device_serial)
            return True
        return False
    except Exception:
        return False
