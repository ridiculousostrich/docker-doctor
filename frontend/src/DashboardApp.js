import React, { useState, useEffect } from 'react';
import './DashboardApp.css';

// API base URL - same host, different port (Flask serves API on 8586, static on 8585)
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8586'
  : `http://${window.location.hostname}:8586`;

function DashboardApp() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState([]);
  const [newErrors, setNewErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, trendsRes, errorsRes] = await Promise.all([
          fetch(`${API_BASE}/api/stats`),
          fetch(`${API_BASE}/api/trends`),
          fetch(`${API_BASE}/api/new-errors`),
        ]);

        if (!statsRes.ok || !trendsRes.ok || !errorsRes.ok) {
          throw new Error('Failed to fetch dashboard data');
        }

        const statsData = await statsRes.json();
        const trendsData = await trendsRes.json();
        const errorsData = await errorsRes.json();

        setStats(statsData);
        setTrends(Array.isArray(trendsData) ? trendsData : []);
        setNewErrors(errorsData);
      } catch (err) {
        setError(err.message);
        // Load mock data as fallback
        loadMockData();
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Fallback mock data if API fails
  const loadMockData = () => {
    setStats({
      date: new Date().toISOString().split('T')[0],
      container_count: 24,
      total_logs: 12048,
      total_errors: 32,
      total_warnings: 47,
      problem_containers: [
        { name: 'nginx-app', error_count: 5, warning_count: 2, ai_summary: 'High error rate in access logs' },
        { name: 'mysql-db', error_count: 3, warning_count: 1, ai_summary: 'Connection pool exhausted' },
        { name: 'redis-cache', error_count: 2, warning_count: 3, ai_summary: 'Cache eviction warnings' },
        { name: 'api-server', error_count: 1, warning_count: 2, ai_summary: 'Slow response times' },
        { name: 'log-rotate', error_count: 0, warning_count: 1, ai_summary: 'Disk space warning' },
      ],
      healthy_containers: [
        { name: 'frontend-app', total_logs: 1200 },
        { name: 'backend-api', total_logs: 890 },
        { name: 'logging-service', total_logs: 450 },
        { name: 'monitoring-tool', total_logs: 200 },
        { name: 'backup-service', total_logs: 150 },
      ],
    });
    setTrends([
      { name: 'cloudflared-tunnel', today: { logs: 6, errors: 6, warnings: 0 }, previous: { logs: 0, errors: 0, warnings: 0 } },
      { name: 'ollama', today: { logs: 286, errors: 11, warnings: 0 }, previous: { logs: 0, errors: 0, warnings: 0 } },
    ]);
    setNewErrors([
      { container_name: 'nginx-app', error_message: '500 Internal Server Error' },
      { container_name: 'mysql-db', error_message: 'Connection timeout' },
    ]);
  };

  if (loading) {
    return (
      <div className="dashboard-app">
        <header className="dashboard-header">
          <h1>Docker Doctor Dashboard v2.0.0</h1>
          <p className="dashboard-subtitle">Loading monitoring data...</p>
        </header>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="dashboard-app">
        <header className="dashboard-header">
          <h1>Docker Doctor Dashboard v2.0.0</h1>
          <p className="dashboard-subtitle" style={{ color: '#e74c3c' }}>Error: {error}</p>
        </header>
      </div>
    );
  }

  return (
    <div className="dashboard-app">
      <header className="dashboard-header">
        <h1>Docker Doctor Dashboard v2.0.0</h1>
        <p className="dashboard-subtitle">Real-time Docker container monitoring system</p>
      </header>

      <nav className="dashboard-nav">
        <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={activeTab === 'containers' ? 'active' : ''} onClick={() => setActiveTab('containers')}>
          Containers
        </button>
        <button className={activeTab === 'trends' ? 'active' : ''} onClick={() => setActiveTab('trends')}>
          Trends
        </button>
        <button className={activeTab === 'reports' ? 'active' : ''} onClick={() => setActiveTab('reports')}>
          Reports
        </button>
      </nav>

      <main className="dashboard-content">
        {activeTab === 'overview' && (
          <OverviewTab stats={stats} newErrors={newErrors} />
        )}
        {activeTab === 'containers' && (
          <ContainersTab stats={stats} />
        )}
        {activeTab === 'trends' && (
          <TrendsTab trends={trends} />
        )}
        {activeTab === 'reports' && (
          <ReportsTab stats={stats} />
        )}
      </main>

      <footer className="dashboard-footer">
        <p>Docker Doctor v2.0.0 - System Health Dashboard</p>
        <p>Last updated: {stats ? stats.date : 'N/A'}</p>
      </footer>
    </div>
  );
}

function OverviewTab({ stats, newErrors }) {
  if (!stats) return null;

  const errorColor = stats.total_errors > 10 ? '#e74c3c' : stats.total_errors > 0 ? '#f39c12' : '#27ae60';
  const warningColor = stats.total_warnings > 20 ? '#e74c3c' : stats.total_warnings > 0 ? '#f39c12' : '#27ae60';

  return (
    <div className="overview-tab">
      <div className="dashboard-stats">
        <div className="stats-card">
          <h3>Containers</h3>
          <p className="stat-number">{stats.container_count}</p>
        </div>
        <div className="stats-card">
          <h3>Total Logs</h3>
          <p className="stat-number">{stats.total_logs?.toLocaleString() || 0}</p>
        </div>
        <div className="stats-card error-card">
          <h3>Errors</h3>
          <p className="stat-number" style={{ color: errorColor }}>{stats.total_errors}</p>
        </div>
        <div className="stats-card warning-card">
          <h3>Warnings</h3>
          <p className="stat-number" style={{ color: warningColor }}>{stats.total_warnings}</p>
        </div>
      </div>

      {stats.problem_containers && stats.problem_containers.length > 0 && (
        <div className="dashboard-section">
          <h2>⚠️ Containers Needing Attention ({stats.problem_containers.length})</h2>
          <div className="containers-table">
            <table>
              <thead>
                <tr>
                  <th>Container</th>
                  <th>Errors</th>
                  <th>Warnings</th>
                  <th>AI Summary</th>
                </tr>
              </thead>
              <tbody>
                {stats.problem_containers.map((c, i) => (
                  <tr key={i} className={c.error_count > 0 ? 'problem-row' : ''}>
                    <td className="container-name">{c.name}</td>
                    <td className="error-cell">{c.error_count}</td>
                    <td className="warning-cell">{c.warning_count}</td>
                    <td className="summary-cell">{c.ai_summary || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {newErrors && newErrors.length > 0 && (
        <div className="dashboard-section">
          <h2>🆕 Recent Errors</h2>
          <div className="recent-errors">
            {newErrors.slice(0, 10).map((e, i) => (
              <div key={i} className="error-card">
                <div className="error-header">
                  <span className="error-container">{e.container_name}</span>
                </div>
                <p className="error-message">{e.error_message?.substring(0, 150)}{e.error_message?.length > 150 ? '...' : ''}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {stats.healthy_containers && stats.healthy_containers.length > 0 && (
        <div className="dashboard-section">
          <h2>✅ Healthy Containers ({stats.healthy_containers.length})</h2>
          <div className="healthy-containers-grid">
            {stats.healthy_containers.slice(0, 8).map((c, i) => (
              <div key={i} className="container-card">
                <h3>{c.name}</h3>
                <p>Logs: {c.total_logs?.toLocaleString() || 'N/A'}</p>
                <p>Status: <span className="status-running">Running</span></p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ContainersTab({ stats }) {
  if (!stats) return <div className="dashboard-section"><p>Loading containers...</p></div>;

  const allContainers = stats.problem_containers || [];
  const healthy = stats.healthy_containers || [];

  return (
    <div className="containers-tab">
      <div className="dashboard-section">
        <h2>All Containers ({(allContainers.length + healthy.length)})</h2>
        <div className="containers-table">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Image</th>
                <th>Errors</th>
                <th>Warnings</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {allContainers.map((c, i) => (
                <tr key={i} className={c.error_count > 0 ? 'problem-row' : ''}>
                  <td className="container-name">{c.name}</td>
                  <td><code>{c.image || 'N/A'}</code></td>
                  <td className="error-cell">{c.error_count}</td>
                  <td className="warning-cell">{c.warning_count}</td>
                  <td>{c.error_count > 0 ? <span className="status-warning">Issues</span> : <span className="status-running">Warning</span>}</td>
                </tr>
              ))}
              {healthy.map((c, i) => (
                <tr key={`h-${i}`}>
                  <td className="container-name">{c.name}</td>
                  <td><code>—</code></td>
                  <td className="error-cell">0</td>
                  <td className="warning-cell">0</td>
                  <td><span className="status-running">Healthy</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function TrendsTab({ trends }) {
  if (!trends || trends.length === 0) {
    return (
      <div className="dashboard-section">
        <h2>Container Health Trends</h2>
        <p>No trend data available yet. Trends will appear after the first daily run.</p>
      </div>
    );
  }

  return (
    <div className="trends-tab">
      <div className="dashboard-section">
        <h2>Error & Warning Trends</h2>
        <div className="trend-table">
          <table>
            <thead>
              <tr>
                <th>Container</th>
                <th>Today Logs</th>
                <th>Today Errors</th>
                <th>Today Warnings</th>
                <th>Prev Errors</th>
                <th>Prev Warnings</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {trends.map((t, i) => {
                const errorsImproved = t.today.errors < t.previous.errors;
                const errorsWorsened = t.today.errors > t.previous.errors;
                const trendIcon = errorsImproved ? '↓' : errorsWorsened ? '↑' : '→';
                const trendColor = errorsImproved ? '#27ae60' : errorsWorsened ? '#e74c3c' : '#7f8c8d';

                return (
                  <tr key={i}>
                    <td className="container-name">{t.name}</td>
                    <td>{t.today?.logs?.toLocaleString() || 0}</td>
                    <td className="error-cell">{t.today?.errors || 0}</td>
                    <td className="warning-cell">{t.today?.warnings || 0}</td>
                    <td>{t.previous?.errors || 0}</td>
                    <td>{t.previous?.warnings || 0}</td>
                    <td style={{ color: trendColor, fontWeight: 'bold' }}>{trendIcon}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ReportsTab({ stats }) {
  return (
    <div className="reports-tab">
      <div className="dashboard-section">
        <h2>Report Actions</h2>
        <div className="report-actions">
          <button className="report-button" onClick={() => alert('PDF export would trigger here - implement with jsPDF or server-side generation')}>
            Export Daily Summary (PDF)
          </button>
          <button className="report-button" onClick={() => {
            // Export as CSV
            if (!stats) return;
            const rows = [
              ['Container', 'Errors', 'Warnings', 'Status'],
              ...(stats.problem_containers?.map(c => [c.name, c.error_count, c.warning_count, c.error_count > 0 ? 'Problem' : 'Warning']) || []),
              ...(stats.healthy_containers?.map(c => [c.name, 0, 0, 'Healthy']) || []),
            ];
            const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `docker-doctor-report-${stats.date || 'latest'}.csv`;
            a.click();
            URL.revokeObjectURL(url);
          }}>
            Export Trends (CSV)
          </button>
          <button className="report-button" onClick={() => alert('Full data export would trigger here')}>
            Export All Data
          </button>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>System Configuration</h2>
        <div className="config-info">
          <p><strong>Database:</strong> data/logs.db</p>
          <p><strong>API Endpoint:</strong> http://localhost:8586/api</p>
          <p><strong>Dashboard Port:</strong> 8585</p>
          <p><strong>Last Update:</strong> {stats?.date || 'N/A'}</p>
        </div>
      </div>
    </div>
  );
}

export default DashboardApp;
