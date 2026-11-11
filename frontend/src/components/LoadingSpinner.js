import React from 'react';

const LoadingSpinner = ({ size = 'medium', text = 'Working...' }) => {
    const sizeClasses = {
        small: 'h-6 w-6',
        medium: 'h-8 w-8',
        large: 'h-12 w-12'
    };

    return (
        <div className="flex flex-col items-center justify-center">
            <div className={`loading-spinner ${sizeClasses[size]}`}></div>
            {text && (
                <p className="mt-4 text-gray-600 text-sm animate-pulse">{text}</p>
            )}
        </div>
    );
};

export default LoadingSpinner; 