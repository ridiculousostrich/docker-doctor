import React, { useState, useEffect } from 'react';
import './Dashboard.css';

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = window.location.hostname === 'localhost'
    ? `${window.location.protocol}//${window.location.hostname}:8586`
    : `${window.location.protocol}//${window.location.hostname}:8586`;

  useEffect(() => {
    fetch(`${API_BASE}/api/stats`)
      .then(response => response.json())
      .then(data => {
        setDashboardData(data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch dashboard data');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="dashboard-error">Error: {error}</div>;
  }

  if (!dashboardData) {
    return <div className="dashboard-loading">No data available</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Docker Doctor Dashboard v2.0.0</h1>
        <p className="dashboard-description">Real-time Docker container monitoring</p>
      </header>

      <div className="dashboard-stats">
        <div className="stats-card">
          <h3>Containers</h3>
          <p className="stat-number">{dashboardData?.container_count || 0}</p>
        </div>
        <div className="stats-card">
          <h3>Total Logs</h3>
          <p className="stat-number">{dashboardData?.total_logs || 0}</p>
        </div>
        <div className="stats-card error-card">
          <h3>Errors</h3>
          <p className="stat-number">{dashboardData?.total_errors || 0}</p>
        </div>
        <div className="stats-card warning-card">
          <h3>Warnings</h3>
          <p className="stat-number">{dashboardData?.total_warnings || 0}</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>Problem Containers</h2>
        {dashboardData.problem_containers && dashboardData.problem_containers.length > 0 ? (
          <div className="containers-table">
            <table>
              <thead>
                <tr>
                  <th>Container Name</th>
                  <th>Errors</th>
                  <th>Warnings</th>
                  <th>AI Summary</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.problem_containers.map((container, index) => (
                  <tr key={index} className={container.error_count > 0 ? 'problem-row' : ''}>
                    <td>{container.name}</td>
                    <td className="error-cell">{container.error_count}</td>
                    <td className="warning-cell">{container.warning_count}</td>
                    <td>{container.ai_summary || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="no-problems">No containers with current issues</p>
        )}
      </div>

      <div className="dashboard-section">
        <h2>Healthy Containers</h2>
        <div className="healthy-containers">
          {dashboardData.healthy_containers?.map((container, index) => (
            <div key={index} className="container-card">
              <h3>{container.name}</h3>
              <p>Logs: {container.total_logs}</p>
            </div>
          ))}
        </div>
      </div>

      <footer className="dashboard-footer">
        <p>Docker Doctor v2.0.0 - System Health Dashboard</p>
        <p>Last updated: {dashboardData.date || 'N/A'}</p>
      </footer>
    </div>
  );
}

export default Dashboard;
