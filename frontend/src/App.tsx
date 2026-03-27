import React, { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Spin } from 'antd';
import { ProjectProvider } from './contexts/ProjectContext';
import { CommandPalette } from './components/ui';
import './components/Layout.css';

const Layout = lazy(() => import('./components/Layout'));
const RequireAuth = lazy(() => import('./components/RequireAuth'));

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Devices = lazy(() => import('./pages/Devices'));
const Elements = lazy(() => import('./pages/Elements'));
const Flows = lazy(() => import('./pages/Flows'));
const LoginPage = lazy(() => import('./pages/Login'));
const Profiles = lazy(() => import('./pages/Profiles'));
const Projects = lazy(() => import('./pages/Projects'));
const Runs = lazy(() => import('./pages/Runs'));
const SchedulerPage = lazy(() => import('./pages/Scheduler'));
const Screens = lazy(() => import('./pages/Screens'));
const Steps = lazy(() => import('./pages/Steps'));
const Suites = lazy(() => import('./pages/Suites'));
const TestPlans = lazy(() => import('./pages/TestPlans'));
const Tags = lazy(() => import('./pages/Tags'));
const Testcases = lazy(() => import('./pages/Testcases'));
const UsersPage = lazy(() => import('./pages/Users'));
const ScheduledJobs = lazy(() => import('./pages/ScheduledJobs'));

const RouteFallback: React.FC = () => (
  <div
    style={{
      minHeight: '40vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <Spin size="large" />
  </div>
);

function App() {
  return (
    <ProjectProvider>
      {/* Global Command Palette */}
      <CommandPalette />

      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<RequireAuth />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="screens" element={<Screens />} />
              <Route path="elements" element={<Elements />} />
              <Route path="steps" element={<Steps />} />
              <Route path="flows" element={<Flows />} />
              <Route path="testcases" element={<Testcases />} />
              <Route path="suites" element={<Suites />} />
              <Route path="test-plans" element={<TestPlans />} />
              <Route path="devices" element={<Devices />} />
              <Route path="profiles" element={<Profiles />} />
              <Route path="tags" element={<Tags />} />
              <Route path="runs" element={<Runs />} />
              <Route path="projects" element={<Projects />} />
              <Route path="scheduled-jobs" element={<ScheduledJobs />} />
              <Route path="scheduler" element={<SchedulerPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ProjectProvider>
  );
}

export default App;
