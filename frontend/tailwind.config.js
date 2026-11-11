/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
        "./public/index.html"
    ],
    theme: {
        extend: {
            colors: {
                // 主色：朱砂
                primary: {
                    50: '#fbf1ec', 100: '#f6dcd2', 200: '#ecb7a4', 300: '#de8a6e',
                    400: '#cc5b3f', 500: '#b3402a', 600: '#9c3521', 700: '#7e2c1d',
                    800: '#65261b', 900: '#4e2018',
                },
                // 辅色：黛青（松烟）
                secondary: {
                    50: '#eef4f2', 100: '#d8e6e1', 200: '#b3ccc4', 300: '#84aba0',
                    400: '#5b8a7e', 500: '#3e6b5f', 600: '#33544d', 700: '#2a453f',
                    800: '#213631', 900: '#182723',
                },
                // 点缀：赭金（只做细线与小标记，不做大面积填充）
                accent: {
                    50: '#faf5e9', 100: '#f1e5c8', 200: '#e3ce97', 300: '#d2b269',
                    400: '#c29e47', 500: '#b08d3e', 600: '#96762f', 700: '#7a6027',
                    800: '#5f4b20', 900: '#463818',
                },
                // 纸与墨
                paper: { DEFAULT: '#f6f1e7', deep: '#efe7d7', card: '#fffdf7' },
                ink: { DEFAULT: '#211d19', soft: '#5a5348', faint: '#8a8175' },
                line: '#e2d8c4',
            },
            fontFamily: {
                serif: ['"Noto Serif SC"', '"Songti SC"', 'STSong', 'SimSun', 'serif'],
                sans: ['"Noto Sans SC"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
                'chinese': ['"Noto Serif SC"', '"Songti SC"', 'SimSun', 'serif'],
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-in-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                }
            }
        },
    },
    plugins: [],
} 