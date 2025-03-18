import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Video,
  Upload,
  LayoutDashboard,
  PenTool,
  Sun,
  Moon,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from './ui/Button';

export const Navigation = ({ toggleTheme, darkMode }) => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white dark:bg-gray-900 border-b dark:border-gray-700 shadow">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <Video className="w-8 h-8 text-red-600 dark:text-red-400" />
            <span className="text-xl font-bold text-gray-800 dark:text-white">
              VideoAI
            </span>
          </Link>

          {/* Menu Items */}
          <div className="hidden md:flex items-center space-x-8">
            {[
              { path: '/upload', icon: <Upload />, label: 'Upload' },
              { path: '/results', icon: <Video />, label: 'Results' },
              { path: '/ad-creatives', icon: <PenTool />, label: 'Ad Creatives' },
              { path: '/dashboard', icon: <LayoutDashboard />, label: 'Dashboard' },
            ].map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-2 ${
                  isActive(item.path)
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400'
                }`}
              >
                <span className="w-5 h-5 text-red-500">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-4">
            {/* Auth Buttons with Glow */}
            <motion.div
              whileHover={{
                scale: 1.1,
                boxShadow: '0 0 12px rgba(255, 0, 0, 0.8)', // Glowing red effect
              }}
            >
              <Button
                variant="outline"
                size="sm"
                className="!text-white bg-red-500 border-red-500 hover:!bg-red-700 hover:!text-white transition-all"
              >
                Sign In
              </Button>
            </motion.div>

            <motion.div
              whileHover={{
                scale: 1.1,
                boxShadow: '0 0 12px rgba(255, 0, 0, 0.8)', // Glowing red effect
              }}
            >
              <Button
                size="sm"
                className="!text-white bg-red-500 border-red-500 hover:!bg-red-700 hover:!text-white transition-all"
              >
                Sign Up
              </Button>
            </motion.div>
          </div>
        </div>
      </div>
    </nav>
  );
};
