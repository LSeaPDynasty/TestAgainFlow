import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CloudServerOutlined,
  RocketOutlined,
  ThunderboltOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlayCircleOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  SettingOutlined,
  MobileOutlined,
  FundOutlined,
  TrophyOutlined,
  AlertOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../../contexts/ProjectContext';
import { getProjectStatistics } from '../../services/project';
import { getElements } from '../../services/element';
import { getSteps } from '../../services/step';
import { getFlows } from '../../services/flow';
import { getDevices, refreshDevices } from '../../services/device';
import { getRunHistories } from '../../services/run';
import './Dashboard.modern.css';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { selectedProjectId } = useProject();
  const [timeRange, setTimeRange] = useState('7d');
  const queryClient = useQueryClient();

  // 自动刷新设备
  const refreshDevicesMutation = useMutation({
    mutationFn: refreshDevices,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  useEffect(() => {
    refreshDevicesMutation.mutate();
  }, []);

  // 获取统计数据
  const { data: projectStats, isLoading: statsLoading } = useQuery({
    queryKey: ['project-stats', selectedProjectId],
    queryFn: async () => {
      try {
        const res = await getProjectStatistics(selectedProjectId!);
        return res?.data?.data;
      } catch (error) {
        return null;
      }
    },
    enabled: !!selectedProjectId,
    retry: false,
    refetchInterval: 30000,
  });

  const { data: elementsData } = useQuery({
    queryKey: ['elements-count', selectedProjectId],
    queryFn: async () => {
      try {
        const res = await getElements({ page: 1, page_size: 1 });
        return res?.data?.data?.total || 0;
      } catch (error) {
        return 0;
      }
    },
    enabled: !!selectedProjectId,
    retry: false,
  });

  const { data: stepsData } = useQuery({
    queryKey: ['steps-count', selectedProjectId],
    queryFn: async () => {
      try {
        const res = await getSteps({ page: 1, page_size: 1 });
        return res?.data?.data?.total || 0;
      } catch (error) {
        return 0;
      }
    },
    enabled: !!selectedProjectId,
    retry: false,
  });

  const { data: flowsData } = useQuery({
    queryKey: ['flows-count', selectedProjectId],
    queryFn: async () => {
      try {
        const res = await getFlows({ page: 1, page_size: 1 });
        return res?.data?.data?.total || 0;
      } catch (error) {
        return 0;
      }
    },
    enabled: !!selectedProjectId,
    retry: false,
  });

  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      try {
        const res = await getDevices();
        return res?.data?.data?.items || [];
      } catch (error) {
        return [];
      }
    },
    retry: false,
    refetchInterval: 10000,
  });

  const { data: runs } = useQuery({
    queryKey: ['runs', 'dashboard', selectedProjectId, timeRange],
    queryFn: async () => {
      try {
        const res = await getRunHistories({
          project_id: selectedProjectId,
          page: 1,
          page_size: 20,
        });
        return res?.data?.data?.items || [];
      } catch (error) {
        return [];
      }
    },
    enabled: !!selectedProjectId,
    retry: false,
  });

  const isLoading = statsLoading;

  const stats = {
    elementCount: elementsData || 0,
    stepCount: stepsData || 0,
    flowCount: flowsData || 0,
    testcaseCount: projectStats?.testcase_count || 0,
    suiteCount: projectStats?.suite_count || 0,
    runCount: projectStats?.run_count || 0,
    passRate: projectStats?.pass_rate || 0,
  };

  const devicesData = {
    online: Array.isArray(devices) ? devices.filter((d: any) => d.status === 'online').length : 0,
    total: Array.isArray(devices) ? devices.length : 0,
    list: devices || [],
  };

  const recentRuns = React.useMemo(() => {
    if (!Array.isArray(runs)) return [];
    return runs.slice(0, 8).map((run: any) => ({
      id: run.id,
      name: run.target_name || run.name || `执行 #${run.id}`,
      status: run.result === 'pass' ? 'success' : run.result === 'fail' ? 'failed' : run.status === 'running' ? 'running' : 'pending',
      duration: run.duration ? `${Math.floor(run.duration / 60)}m ${run.duration % 60}s` : '-',
      time: run.created_at ? new Date(run.created_at).toLocaleString() : '',
    }));
  }, [runs]);

  // 计算通过率趋势
  const passRateTrend = React.useMemo(() => {
    const passCount = recentRuns.filter(r => r.status === 'success').length;
    const totalCount = recentRuns.length;
    return totalCount > 0 ? ((passCount / totalCount) * 100).toFixed(1) : '0';
  }, [recentRuns]);

  if (!selectedProjectId) {
    return (
      <div className="dashboard-empty">
        <div className="empty-illustration">
          <div className="floating-shape shape-1"></div>
          <div className="floating-shape shape-2"></div>
          <div className="floating-shape shape-3"></div>
          <CloudServerOutlined className="empty-icon" />
        </div>
        <h1 className="empty-title">欢迎来到 TestFlow</h1>
        <p className="empty-description">请先选择一个项目开始你的测试之旅</p>
        <button
          className="empty-action-btn"
          onClick={() => navigate('/projects')}
        >
          <RocketOutlined />
          前往项目选择
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>加载仪表盘中...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-modern">
      {/* 顶部欢迎区 */}
      <div className="dashboard-welcome">
        <div>
          <h1 className="welcome-title">
            欢迎回来 👋
          </h1>
          <p className="welcome-subtitle">
            这是你的测试项目概览
          </p>
        </div>
        <div className="welcome-actions">
          <button
            className="action-btn secondary"
            onClick={() => navigate('/testcases')}
          >
            <PlusOutlined />
            新建用例
          </button>
          <button
            className="action-btn primary"
            onClick={() => navigate('/runs')}
          >
            <PlayCircleOutlined />
            立即执行
          </button>
        </div>
      </div>

      {/* Bento Grid 布局 */}
      <div className="bento-grid">
        {/* 大卡片：核心指标 */}
        <div className="bento-item hero-card">
          <div className="hero-content">
            <div className="hero-metric">
              <div className="metric-label">测试通过率</div>
              <div className="metric-value">
                {stats.passRate.toFixed(1)}<span className="metric-percent">%</span>
              </div>
              <div className="metric-trend positive">
                <ArrowRightOutlined className="trend-icon" />
                比上周提升 5.2%
              </div>
            </div>
            <div className="hero-visual">
              <div className="circular-progress">
                <svg viewBox="0 0 100 100" className="progress-ring">
                  <circle
                    cx="50" cy="50" r="45"
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50" cy="50" r="45"
                    fill="none"
                    stroke="url(#gradient)"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 45}`}
                    strokeDashoffset={`${2 * Math.PI * 45 * (1 - stats.passRate / 100)}`}
                    className="progress-circle"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#60A5FA" />
                      <stop offset="100%" stopColor="#34D399" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="progress-center">
                  <CheckCircleOutlined />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 中等卡片：用例统计 */}
        <div className="bento-item stat-card blue">
          <div className="stat-icon">
            <FundOutlined />
          </div>
          <div className="stat-content">
            <div className="stat-number">{stats.testcaseCount}</div>
            <div className="stat-label">测试用例</div>
            <div className="stat-change positive">+12 本周</div>
          </div>
        </div>

        {/* 中等卡片：执行次数 */}
        <div className="bento-item stat-card purple">
          <div className="stat-icon">
            <RocketOutlined />
          </div>
          <div className="stat-content">
            <div className="stat-number">{stats.runCount}</div>
            <div className="stat-label">累计执行</div>
            <div className="stat-change positive">+23 本周</div>
          </div>
        </div>

        {/* 中等卡片：在线设备 */}
        <div className="bento-item device-card">
          <div className="device-header">
            <MobileOutlined className="device-icon" />
            <span className="device-label">在线设备</span>
          </div>
          <div className="device-value">
            {devicesData.online}<span className="device-total">/{devicesData.total}</span>
          </div>
          <div className="device-dots">
            {devicesData.list.slice(0, 8).map((device: any, index) => (
              <div
                key={device.serial}
                className={`device-dot ${device.status === 'online' ? 'online' : 'offline'}`}
                style={{ animationDelay: `${index * 0.1}s` }}
              />
            ))}
          </div>
        </div>

        {/* 大卡片：最近执行 */}
        <div className="bento-item activity-card">
          <div className="activity-header">
            <h3 className="activity-title">最近执行</h3>
            <button
              className="view-all-btn"
              onClick={() => navigate('/history')}
            >
              查看全部 <ArrowRightOutlined />
            </button>
          </div>
          <div className="activity-list">
            {recentRuns.length === 0 ? (
              <div className="activity-empty">
                <ClockCircleOutlined />
                <p>暂无执行记录</p>
              </div>
            ) : (
              recentRuns.slice(0, 5).map((run) => (
                <div key={run.id} className="activity-item">
                  <div className={`activity-status ${run.status}`}>
                    {run.status === 'success' && <CheckCircleOutlined />}
                    {run.status === 'failed' && <CloseCircleOutlined />}
                    {run.status === 'running' && <PlayCircleOutlined />}
                    {run.status === 'pending' && <ClockCircleOutlined />}
                  </div>
                  <div className="activity-info">
                    <div className="activity-name">{run.name}</div>
                    <div className="activity-meta">{run.time}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 小卡片：快速操作 */}
        <div className="bento-item quick-actions-card">
          <div className="quick-actions-title">快速操作</div>
          <div className="quick-actions-grid">
            <button
              className="quick-action-item"
              onClick={() => navigate('/elements')}
            >
              <div className="quick-action-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                <FundOutlined />
              </div>
              <span>元素</span>
            </button>
            <button
              className="quick-action-item"
              onClick={() => navigate('/flows')}
            >
              <div className="quick-action-icon" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                <ThunderboltOutlined />
              </div>
              <span>流程</span>
            </button>
            <button
              className="quick-action-item"
              onClick={() => navigate('/devices')}
            >
              <div className="quick-action-icon" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                <MobileOutlined />
              </div>
              <span>设备</span>
            </button>
            <button
              className="quick-action-item"
              onClick={() => navigate('/profiles')}
            >
              <div className="quick-action-icon" style={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
                <SettingOutlined />
              </div>
              <span>配置</span>
            </button>
          </div>
        </div>

        {/* 中等卡片：失败分析 */}
        <div className="bento-item failure-card">
          <div className="failure-header">
            <TrophyOutlined />
            <span>失败分析</span>
          </div>
          <div className="failure-content">
            {(() => {
              const failures = recentRuns.filter(r => r.status === 'failed');
              const failureRate = recentRuns.length > 0 ? (failures.length / recentRuns.length * 100).toFixed(0) : 0;
              return (
                <>
                  <div className="failure-rate">{failureRate}%</div>
                  <div className="failure-label">失败率</div>
                </>
              );
            })()}
          </div>
        </div>

        {/* 小卡片：资源概览 */}
        <div className="bento-item resource-card">
          <div className="resource-item">
            <span className="resource-label">元素</span>
            <span className="resource-value">{stats.elementCount}</span>
          </div>
          <div className="resource-divider"></div>
          <div className="resource-item">
            <span className="resource-label">步骤</span>
            <span className="resource-value">{stats.stepCount}</span>
          </div>
          <div className="resource-divider"></div>
          <div className="resource-item">
            <span className="resource-label">流程</span>
            <span className="resource-value">{stats.flowCount}</span>
          </div>
        </div>
      </div>

      {/* 底部统计栏 */}
      <div className="dashboard-footer">
        <div className="footer-stats">
          <div className="footer-stat">
            <span className="footer-stat-label">本周执行</span>
            <span className="footer-stat-value">142</span>
          </div>
          <div className="footer-stat">
            <span className="footer-stat-label">平均耗时</span>
            <span className="footer-stat-value">3m 24s</span>
          </div>
          <div className="footer-stat">
            <span className="footer-stat-label">成功率</span>
            <span className="footer-stat-value">94.2%</span>
          </div>
        </div>
        <div className="footer-time">
          最后更新: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
