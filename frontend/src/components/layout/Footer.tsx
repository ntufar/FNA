/**
 * Application Footer Component
 * 
 * Contains copyright, links, and application information.
 */

import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Copyright and Version Info */}
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>© {currentYear} FNA Platform</span>
            <span>•</span>
            <span>Version 1.0.0</span>
            <span>•</span>
            <span className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              System Healthy
            </span>
          </div>

          {/* Footer Links */}
          <div className="flex items-center space-x-6 text-sm">
            <Link
              to="/help"
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              Help Center
            </Link>
            
            <Link
              to="/api-docs"
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              API Docs
            </Link>
            
            <Link
              to="/privacy"
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              Privacy Policy
            </Link>
            
            <a
              href="mailto:support@fnaplatform.com"
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              Support
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
