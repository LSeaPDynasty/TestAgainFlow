import { useEffect } from 'react';

/**
 * Hook for registering keyboard shortcuts
 * @param keys - Key combination (e.g., 'k', '/', 'n')
 * @param callback - Function to execute when shortcut is triggered
 * @param options - Options for the hotkey
 */
export function useHotkeys(
  keys: string,
  callback: () => void,
  options?: {
    preventDefault?: boolean;
    disabled?: boolean;
  }
) {
  useEffect(() => {
    if (options?.disabled) return;

    const handler = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      // Check for modifier + key combination
      if (modKey && e.key.toLowerCase() === keys.toLowerCase()) {
        if (options?.preventDefault !== false) {
          e.preventDefault();
        }
        callback();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [keys, callback, options]);
}

/**
 * Hook for Escape key shortcut
 */
export function useEscapeShortcut(callback: () => void, disabled?: boolean) {
  useEffect(() => {
    if (disabled) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        callback();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [callback, disabled]);
}
