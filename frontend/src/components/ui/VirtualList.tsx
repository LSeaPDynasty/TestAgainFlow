import React, { useRef } from 'react';
import { useVirtualList } from '../../hooks/useVirtualList';

export interface VirtualListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  className?: string;
}

/**
 * VirtualList Component
 *
 * Optimizes rendering of large lists by only rendering visible items.
 * This improves performance significantly for lists with 1000+ items.
 *
 * @example
 * ```tsx
 * <VirtualList
 *   items={elements}
 *   height={600}
 *   itemHeight={55}
 *   renderItem={(item, index) => (
 *     <div key={item.id}>{item.name}</div>
 *   )}
 * />
 * ```
 */
export function VirtualList<T>({
  items,
  height,
  itemHeight,
  renderItem,
  overscan = 5,
  className,
}: VirtualListProps<T>) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { virtualItems, totalSize } = useVirtualList({
    count: items.length,
    estimateSize: itemHeight,
    getScrollElement: () => scrollRef.current,
    overscan,
  });

  return (
    <div
      ref={scrollRef}
      className={className}
      style={{
        height,
        overflow: 'auto',
      }}
    >
      <div
        style={{
          height: `${totalSize}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualRow) => {
          const item = items[virtualRow.index];
          if (!item) return null;

          return (
            <div
              key={virtualRow.key}
              data-index={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${itemHeight}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              {renderItem(item, virtualRow.index)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * VirtualTable Component
 *
 * A table-like virtualized list with fixed header.
 *
 * @example
 * ```tsx
 * <VirtualTable
 *   items={elements}
 *   height={600}
 *   itemHeight={55}
 *   columns={[
 *     { key: 'name', title: 'Name', width: 200 },
 *     { key: 'value', title: 'Value', width: 150 },
 *   ]}
 *   renderItem={(item) => (
 *     <tr>
 *       <td>{item.name}</td>
 *       <td>{item.value}</td>
 *     </tr>
 *   )}
 * />
 * ```
 */
export interface VirtualTableProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  columns: Array<{
    key: string;
    title: string;
    width?: number;
    render?: (item: T, index: number) => React.ReactNode;
  }>;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  className?: string;
}

export function VirtualTable<T>({
  items,
  height,
  itemHeight,
  columns,
  renderItem,
  overscan = 5,
  className,
}: VirtualTableProps<T>) {
  const headerHeight = 40;

  return (
    <div className={className}>
      {/* Header */}
      <div
        className="bg-gray-50 border-b border-gray-200"
        style={{ height: headerHeight }}
      >
        <table className="w-full">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-2 text-left text-sm font-medium text-gray-600"
                  style={{ width: col.width }}
                >
                  {col.title}
                </th>
              ))}
            </tr>
          </thead>
        </table>
      </div>

      {/* Virtual Body */}
      <VirtualList
        items={items}
        height={height - headerHeight}
        itemHeight={itemHeight}
        renderItem={renderItem}
        overscan={overscan}
      />
    </div>
  );
}

export default VirtualList;
