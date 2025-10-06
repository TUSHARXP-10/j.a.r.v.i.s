import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Navigation.css';

const Navigation = ({ activeView, setActiveView }) => {
  const { user, logout, hasRole, hasAnyRole } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
  };

  const handleViewChange = (view) => {
    setActiveView(view);
    setShowUserMenu(false);
  };

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h1>Workflow Manager</h1>
      </div>
      
      <div className="nav-links">
        <button
          className={`nav-link ${activeView === 'workflows' ? 'active' : ''}`}
          onClick={() => handleViewChange('workflows')}
        >
          Workflows
        </button>
        
        <button
          className={`nav-link ${activeView === 'schedules' ? 'active' : ''}`}
          onClick={() => handleViewChange('schedules')}
        >
          Schedules
        </button>
        
        {hasRole('admin') && (
          <button
            className={`nav-link ${activeView === 'users' ? 'active' : ''}`}
            onClick={() => handleViewChange('users')}
          >
            Users
          </button>
        )}
      </div>
      
      <div className="nav-user">
        <div className="user-info">
          <span className="username">{user?.username}</span>
          <span className={`role-badge role-${user?.role}`}>
            {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
          </span>
        </div>
        
        <div className="user-menu">
          <button
            className="user-menu-toggle"
            onClick={() => setShowUserMenu(!showUserMenu)}
          >
            <span className="user-avatar">{user?.username?.charAt(0)?.toUpperCase()}</span>
            <span className="dropdown-arrow">▼</span>
          </button>
          
          {showUserMenu && (
            <div className="user-menu-dropdown">
              <div className="user-menu-header">
                <div className="user-menu-avatar">{user?.username?.charAt(0)?.toUpperCase()}</div>
                <div className="user-menu-info">
                  <div className="user-menu-name">{user?.username}</div>
                  <div className="user-menu-email">{user?.email}</div>
                  <div className={`user-menu-role role-${user?.role}`}>
                    {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
                  </div>
                </div>
              </div>
              
              <div className="user-menu-actions">
                <button 
                  className="user-menu-item"
                  onClick={() => setShowUserMenu(false)}
                >
                  Profile Settings
                </button>
                <button 
                  className="user-menu-item"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

// Protected Route Component
export const ProtectedRoute = ({ children, requiredRoles = [] }) => {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div className="auth-required">Please login to access this content.</div>;
  }

  if (requiredRoles.length > 0 && !hasAnyRole(requiredRoles)) {
    return (
      <div className="access-denied">
        <h3>Access Denied</h3>
        <p>You don't have permission to access this content.</p>
      </div>
    );
  }

  return children;
};

export default Navigation;