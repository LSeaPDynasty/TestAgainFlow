import React from 'react';
import { Select } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { getProjects, type Project } from '../../services/project';

const { Option } = Select;

interface ProjectSelectorProps {
  value?: number | null;
  onChange?: (projectId: number | null) => void;
  placeholder?: string;
  allowClear?: boolean;
  style?: React.CSSProperties;
}

const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  value,
  onChange,
  placeholder = "选择项目",
  allowClear = true,
  style = {},
}) => {
  // 获取项目列表
  const { data: projectsData, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => getProjects({ page: 1, page_size: 100 }),
  });

  const projects = projectsData?.data?.data?.items || [];

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      allowClear={allowClear}
      loading={isLoading}
      style={{ width: 250, ...style }}
      showSearch
      optionFilterProp="children"
    >
      {projects.map((project: Project) => (
        <Option key={project.id} value={project.id}>
          {project.name}
        </Option>
      ))}
    </Select>
  );
};

export default ProjectSelector;
