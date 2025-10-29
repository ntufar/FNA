/**
 * Authentication Context for FNA Platform
 * 
 * Provides authentication state management, user session handling,
 * and authentication-related functionality across the application.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'react-toastify';
import { apiClient, User, LoginRequest, RegisterRequest, AuthResponse } from '../services/api';

interface AuthContextType {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  
  // Utilities
  hasPermission: (requiredTier: string) => boolean;
  isSubscriptionActive: () => boolean;
}

interface AuthProviderProps {
  children: ReactNode;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      setIsLoading(true);
      
      // Check if user is already authenticated
      if (apiClient.isAuthenticated()) {
        const storedUser = apiClient.getCurrentUserFromStorage();
        
        if (storedUser) {
          setUser(storedUser);
          // Refresh user data from server to ensure it's current
          await refreshUser();
        } else {
          // Token exists but no user data, fetch from server
          await refreshUser();
        }
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error);
      // Clear invalid session
      await logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      setIsLoading(true);
      
      const authResponse: AuthResponse = await apiClient.login(credentials);
      setUser(authResponse.user);
      
      toast.success(`Welcome back, ${authResponse.user.email}!`);
    } catch (error: any) {
      console.error('Login failed:', error);
      const errorMessage = error.response?.data?.error?.message || 'Login failed';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest): Promise<void> => {
    try {
      setIsLoading(true);
      
      const authResponse: AuthResponse = await apiClient.register(userData);
      setUser(authResponse.user);
      
      toast.success(`Account created successfully! Welcome, ${authResponse.user.email}`);
    } catch (error: any) {
      console.error('Registration failed:', error);
      const errorMessage = error.response?.data?.error?.message || 'Registration failed';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      toast.info('You have been logged out');
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails, user session is likely invalid
      setUser(null);
      throw error;
    }
  };

  const hasPermission = (requiredTier: string): boolean => {
    if (!user) return false;
    
    const tierHierarchy: Record<string, number> = {
      'Basic': 1,
      'Pro': 2,
      'Enterprise': 3,
    };
    
    const userTierLevel = tierHierarchy[user.subscription_tier] || 0;
    const requiredTierLevel = tierHierarchy[requiredTier] || 0;
    
    return userTierLevel >= requiredTierLevel;
  };

  const isSubscriptionActive = (): boolean => {
    return user?.is_active || false;
  };

  const contextValue: AuthContextType = {
    // State
    user,
    isAuthenticated: !!user && isSubscriptionActive(),
    isLoading,
    
    // Actions
    login,
    register,
    logout,
    refreshUser,
    
    // Utilities
    hasPermission,
    isSubscriptionActive,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// HOC for protected routes
export interface WithAuthProps {
  requiredTier?: string;
}

export const withAuth = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: WithAuthProps = {}
) => {
  const AuthenticatedComponent: React.FC<P> = (props) => {
    const { isAuthenticated, isLoading, hasPermission, user } = useAuth();
    const { requiredTier } = options;

    // Show loading spinner while checking authentication
    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Authentication Required</h2>
            <p className="mb-4">Please log in to access this page.</p>
            <button
              onClick={() => window.location.href = '/login'}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Go to Login
            </button>
          </div>
        </div>
      );
    }

    // Check subscription tier requirements
    if (requiredTier && !hasPermission(requiredTier)) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Upgrade Required</h2>
            <p className="mb-4">
              This feature requires a {requiredTier} subscription.
              Your current tier: {user?.subscription_tier}
            </p>
            <button
              onClick={() => window.location.href = '/upgrade'}
              className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700"
            >
              Upgrade Subscription
            </button>
          </div>
        </div>
      );
    }

    return <WrappedComponent {...props} />;
  };

  AuthenticatedComponent.displayName = `withAuth(${WrappedComponent.displayName || WrappedComponent.name})`;
  
  return AuthenticatedComponent;
};

export default AuthProvider;
