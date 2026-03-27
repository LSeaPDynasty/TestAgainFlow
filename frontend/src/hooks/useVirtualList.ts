import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

/**
 * Hook for creating a virtualized list
 * Optimizes rendering of large lists by only rendering visible items
 *
 * @param options - Configuration options for the virtual list
 * @returns Virtual list instance and ref for the scroll element
 */
export function useVirtualList<T>(options: {
  count: number;
  estimateSize?: number;
  getScrollElement: () => HTMLElement | null;
  overscan?: number;
}) {
  const {
    count,
    estimateSize = 50,
    getScrollElement,
    overscan = 5,
  } = options;

  const virtualizer = useVirtualizer({
    count,
    getScrollElement,
    estimateSize: () => estimateSize,
    overscan,
  });

  return {
    virtualizer,
    virtualItems: virtualizer.getVirtualItems(),
    totalSize: virtualizer.getTotalSize(),
  };
}

/**
 * Hook for creating a virtualized row list (horizontal)
 */
export function useVirtualRowList(options: {
  count: number;
  estimateSize?: number;
  getScrollElement: () => HTMLElement | null;
  overscan?: number;
}) {
  const {
    count,
    estimateSize = 100,
    getScrollElement,
    overscan = 5,
  } = options;

  const virtualizer = useVirtualizer({
    count,
    getScrollElement,
    estimateSize: () => estimateSize,
    overscan,
    horizontal: true,
  });

  return {
    virtualizer,
    virtualItems: virtualizer.getVirtualItems(),
    totalSize: virtualizer.getTotalSize(),
  };
}
