import React, { createContext, useContext, useState, useEffect } from 'react';

interface ProjectContextType {
  selectedProjectId: number | null;
  setSelectedProjectId: (projectId: number | null) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // 从 localStorage 读取上次选择的项目
  const [selectedProjectId, setSelectedProjectIdState] = useState<number | null>(() => {
    const saved = localStorage.getItem('selectedProjectId');
    return saved ? parseInt(saved) : null;
  });

  const setSelectedProjectId = (projectId: number | null) => {
    setSelectedProjectIdState(projectId);
    if (projectId !== null) {
      localStorage.setItem('selectedProjectId', projectId.toString());
    } else {
      localStorage.removeItem('selectedProjectId');
    }
  };

  return (
    <ProjectContext.Provider value={{ selectedProjectId, setSelectedProjectId }}>
      {children}
    </ProjectContext.Provider>
  );
};
