import React from 'react';
import { Zap } from 'lucide-react';

const Header = () => {
  return (
    <div className="bg-indigo-600 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Zap className="text-white" size={24} />
          <h1 className="text-xl font-bold text-white">Product Manager Enhancer</h1>
        </div>
        <div className="text-indigo-100 text-sm">
          AI-powered product enhancement agent
        </div>
      </div>
    </div>
  );
};

export default Header; 