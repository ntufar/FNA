/**
 * Application Router for FNA Platform
 * 
 * Defines all application routes, protected routes, and navigation structure.
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Layout from '../components/layout/Layout';
import ErrorBoundary from '../components/common/ErrorBoundary';

// Lazy load components for code splitting
const HomePage = lazy(() => import('../pages/HomePage'));
const LoginPage = lazy(() => import('../pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('../pages/auth/RegisterPage'));
const DashboardPage = lazy(() => import('../pages/DashboardPage'));
const CompaniesPage = lazy(() => import('../pages/CompaniesPage'));
const ReportsPage = lazy(() => import('../pages/ReportsPage'));
const AnalysisPage = lazy(() => import('../pages/AnalysisPage'));
const ComparisonPage = lazy(() => import('../pages/ComparisonPage'));
const AlertsPage = lazy(() => import('../pages/AlertsPage'));
const SettingsPage = lazy(() => import('../pages/SettingsPage'));
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'));

// Route configuration interface
interface RouteConfig {
  path: string;
  element: React.ComponentType<any>;
  requiresAuth?: boolean;
  requiredTier?: string;
  layout?: boolean;
}

// Define application routes
const routes: RouteConfig[] = [
  // Public routes
  {
    path: '/',
    element: HomePage,
    layout: false,
  },
  {
    path: '/login',
    element: LoginPage,
    layout: false,
  },
  {
    path: '/register',
    element: RegisterPage,
    layout: false,
  },
  
  // Protected routes (require authentication)
  {
    path: '/dashboard',
    element: DashboardPage,
    requiresAuth: true,
    layout: true,
  },
  {
    path: '/companies',
    element: CompaniesPage,
    requiresAuth: true,
    layout: true,
  },
  {
    path: '/reports',
    element: ReportsPage,
    requiresAuth: true,
    layout: true,
  },
  {
    path: '/analysis',
    element: AnalysisPage,
    requiresAuth: true,
    layout: true,
  },
  {
    path: '/comparison',
    element: ComparisonPage,
    requiresAuth: true,
    layout: true,
  },
  {
    path: '/alerts',
    element: AlertsPage,
    requiresAuth: true,
    layout: true,
  },
  {
    path: '/settings',
    element: SettingsPage,
    requiresAuth: true,
    layout: true,
  },
];

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiresAuth?: boolean;
  requiredTier?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiresAuth = false,
  requiredTier,
}) => {
  const { isAuthenticated, isLoading, hasPermission, user } = useAuth();

  // Show loading while checking authentication
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Check authentication requirement
  if (requiresAuth && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check subscription tier requirement
  if (requiredTier && (!isAuthenticated || !hasPermission(requiredTier))) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-white shadow-lg rounded-lg p-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-yellow-100 rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-yellow-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m0 0v2m0-2h2m-2 0H10m9-7a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Upgrade Required
            </h2>
            
            <p className="text-gray-600 mb-6">
              This feature requires a {requiredTier} subscription.
              {user && (
                <> Your current tier: <strong>{user.subscription_tier}</strong></>
              )}
            </p>
            
            <div className="space-y-3">
              <button
                onClick={() => window.location.href = '/settings/subscription'}
                className="w-full bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors"
              >
                Upgrade Subscription
              </button>
              
              <button
                onClick={() => window.history.back()}
                className="w-full bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

// Auth Redirect Component (redirects authenticated users away from auth pages)
const AuthRedirect: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Redirect authenticated users to dashboard
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Layout Wrapper Component
interface LayoutWrapperProps {
  children: React.ReactNode;
  useLayout: boolean;
}

const LayoutWrapper: React.FC<LayoutWrapperProps> = ({ children, useLayout }) => {
  if (useLayout) {
    return <Layout>{children}</Layout>;
  }
  return <>{children}</>;
};

// Main App Router Component
const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {routes.map((route) => {
              const { path, element: Component, requiresAuth, requiredTier, layout } = route;
              
              // Determine if this is an auth page
              const isAuthPage = path === '/login' || path === '/register';
              
              return (
                <Route
                  key={path}
                  path={path}
                  element={
                    <LayoutWrapper useLayout={layout || false}>
                      {isAuthPage ? (
                        <AuthRedirect>
                          <Component />
                        </AuthRedirect>
                      ) : (
                        <ProtectedRoute
                          requiresAuth={requiresAuth}
                          requiredTier={requiredTier}
                        >
                          <Component />
                        </ProtectedRoute>
                      )}
                    </LayoutWrapper>
                  }
                />
              );
            })}
            
            {/* Default redirects */}
            <Route
              path="/app"
              element={<Navigate to="/dashboard" replace />}
            />
            
            {/* 404 Not Found */}
            <Route
              path="*"
              element={
                <LayoutWrapper useLayout={false}>
                  <NotFoundPage />
                </LayoutWrapper>
              }
            />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </BrowserRouter>
  );
};

export default AppRouter;
