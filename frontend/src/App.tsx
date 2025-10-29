/**
 * Main App Component for FNA Platform
 * 
 * Root component that sets up providers, routing, and global configuration.
 */

import React from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { AuthProvider } from './contexts/AuthContext';
import AppRouter from './router/AppRouter';

const App: React.FC = () => {
  return (
    <div className="App">
      {/* Authentication Provider */}
      <AuthProvider>
        {/* Main Router */}
        <AppRouter />
        
        {/* Toast Notifications */}
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="light"
          className="toast-container"
        />
      </AuthProvider>
    </div>
  );
};

export default App;
