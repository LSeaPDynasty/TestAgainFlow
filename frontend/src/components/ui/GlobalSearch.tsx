import React, { useState, useCallback, useEffect } from 'react';
import { Input, AutoComplete, Badge, Space, Typography } from 'antd';
import {
  SearchOutlined,
  AppstoreOutlined,
  BlockOutlined,
  TransactionOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useHotkeys } from '../../hooks/useHotkeys';
import { useDebounce } from '../../hooks/useDebounce';

// TODO: Implement search functions in services
// For now, we'll use a placeholder
const searchElements = async (query: string) => [];
const searchSteps = async (query: string) => [];
const searchFlows = async (query: string) => [];
const searchTestcases = async (query: string) => [];

const { Text } = Typography;

export interface SearchResult {
  id: string;
  type: 'element' | 'step' | 'flow' | 'testcase';
  name: string;
  description?: string;
  path: string;
  icon: React.ReactNode;
}

interface SearchOption {
  value: string;
  label: React.ReactNode;
  result: SearchResult;
}

export interface GlobalSearchProps {
  className?: string;
}

export const GlobalSearch: React.FC<GlobalSearchProps> = ({ className }) => {
  const [searchText, setSearchText] = useState('');
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<SearchOption[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const debouncedSearch = useDebounce(searchText, 300);

  // Open search with Ctrl+/ or Cmd+/
  useHotkeys('/', () => {
    setOpen(true);
    // Focus input after opening
    setTimeout(() => {
      const input = document.querySelector('.global-search-input') as HTMLInputElement;
      input?.focus();
    }, 100);
  }, { preventDefault: true });

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
        setSearchText('');
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [open]);

  // Perform search
  useEffect(() => {
    const performSearch = async () => {
      if (!debouncedSearch || debouncedSearch.length < 2) {
        setOptions([]);
        return;
      }

      setLoading(true);
      try {
        const results: SearchResult[] = [];

        // Search elements
        const elements = await searchElements(debouncedSearch);
        results.push(...(elements || []).map((el: any) => ({
          id: `element-${el.id}`,
          type: 'element' as const,
          name: el.name,
          description: el.selector,
          path: `/elements`,
          icon: <AppstoreOutlined />,
        })));

        // Search steps
        const steps = await searchSteps(debouncedSearch);
        results.push(...(steps || []).map((step: any) => ({
          id: `step-${step.id}`,
          type: 'step' as const,
          name: step.name,
          description: step.action_type,
          path: `/steps`,
          icon: <BlockOutlined />,
        })));

        // Search flows
        const flows = await searchFlows(debouncedSearch);
        results.push(...(flows || []).map((flow: any) => ({
          id: `flow-${flow.id}`,
          type: 'flow' as const,
          name: flow.name,
          description: flow.description,
          path: `/flows`,
          icon: <TransactionOutlined />,
        })));

        // Search testcases
        const testcases = await searchTestcases(debouncedSearch);
        results.push(...(testcases || []).map((tc: any) => ({
          id: `testcase-${tc.id}`,
          type: 'testcase' as const,
          name: tc.name,
          description: tc.description,
          path: `/testcases`,
          icon: <FileTextOutlined />,
        })));

        // Convert to AutoComplete options
        const searchOptions: SearchOption[] = results.slice(0, 10).map((result) => ({
          value: result.id,
          label: (
            <div className="flex items-center justify-between py-1">
              <Space>
                {result.icon}
                <div>
                  <div className="font-medium">{result.name}</div>
                  {result.description && (
                    <Text type="secondary" className="text-xs">
                      {result.description}
                    </Text>
                  )}
                </div>
              </Space>
              <Badge
                count={result.type}
                style={{
                  fontSize: '10px',
                  padding: '0 4px',
                  height: '18px',
                  lineHeight: '18px',
                }}
              />
            </div>
          ),
          result,
        }));

        setOptions(searchOptions);
      } catch (error) {
        console.error('Search failed:', error);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [debouncedSearch]);

  const handleSelect = useCallback(
    (_value: string, option: SearchOption) => {
      navigate(option.result.path);
      setOpen(false);
      setSearchText('');
    },
    [navigate]
  );

  return (
    <AutoComplete
      className={`global-search-input ${className || ''}`}
      style={{ width: '100%', minWidth: 300 }}
      options={options}
      onSearch={setSearchText}
      onSelect={handleSelect}
      open={open}
      onDropdownVisibleChange={setOpen}
      placeholder="Search elements, steps, flows, testcases... (Ctrl+/)"
      notFoundContent={loading ? 'Searching...' : 'No results found'}
      value={searchText}
      popupClassName="global-search-dropdown"
    >
      <Input
        size="large"
        prefix={<SearchOutlined />}
        suffix={
          <Text type="secondary" className="text-xs">
            Ctrl+/
          </Text>
        }
      />
    </AutoComplete>
  );
};

export default GlobalSearch;
