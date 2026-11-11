import React from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const ChartCard = ({
    title,
    subtitle,
    color = 'primary',
    children,
    isExpanded = true,
    onToggle
}) => {
    const colorStyles = {
        primary: {
            border: 'border-primary-200',
            bg: 'bg-primary-50',
            text: 'text-primary-800',
            accent: 'text-primary-600'
        },
        secondary: {
            border: 'border-secondary-200',
            bg: 'bg-secondary-50',
            text: 'text-secondary-800',
            accent: 'text-secondary-600'
        },
        accent: {
            border: 'border-accent-200',
            bg: 'bg-accent-50',
            text: 'text-accent-800',
            accent: 'text-accent-600'
        }
    };

    const styles = colorStyles[color];

    return (
        <div className={`chart-card ${styles.border}`}>
            <div
                className={`flex items-center justify-between cursor-pointer ${styles.bg} -m-6 mb-4 p-4 rounded-t-xl`}
                onClick={onToggle}
            >
                <div>
                    <h3 className={`text-lg font-bold ${styles.text}`}>{title}</h3>
                    <p className={`text-sm ${styles.accent}`}>{subtitle}</p>
                </div>

                {onToggle && (
                    <button className={`p-1 rounded-full hover:bg-white/50 transition-colors duration-200 ${styles.text}`}>
                        {isExpanded ? (
                            <ChevronUp className="w-5 h-5" />
                        ) : (
                            <ChevronDown className="w-5 h-5" />
                        )}
                    </button>
                )}
            </div>

            {isExpanded && (
                <div className="animate-fade-in">
                    {children}
                </div>
            )}
        </div>
    );
};

export default ChartCard; 