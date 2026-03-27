/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 品牌色 - 科技蓝
        primary: {
          50: '#E6F4FF',
          100: '#BAE0FF',
          200: '#91CAFF',
          300: '#69B1FF',
          400: '#4096FF',
          500: '#1677FF',
          600: '#0958D9',
          700: '#003EB3',
          800: '#002C8C',
          900: '#001D66',
        },
        // 语义色
        success: '#52C41A',
        warning: '#FAAD14',
        error: '#FF4D4F',
        info: '#1677FF',
        // 测试专用色
        test: {
          p0: '#FF4D4F',
          p1: '#FAAD14',
          p2: '#FADB14',
          p3: '#8C8C8C',
          running: '#1677FF',
          pending: '#8C8C8C',
        },
        // 中性色
        gray: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#E8E8E8',
          300: '#D9D9D9',
          400: '#BFBFBF',
          500: '#8C8C8C',
          600: '#595959',
          700: '#434343',
          800: '#262626',
          900: '#1F1F1F',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      fontSize: {
        xs: '0.75rem',    // 12px
        sm: '0.875rem',   // 14px
        base: '1rem',     // 16px
        lg: '1.125rem',   // 18px
        xl: '1.25rem',    // 20px
        '2xl': '1.5rem',  // 24px
        '3xl': '1.875rem', // 30px
        '4xl': '2.25rem', // 36px
      },
      spacing: {
        18: '4.5rem',
        88: '22rem',
      },
      borderRadius: {
        'none': '0',
        'sm': '0.25rem',   // 4px
        'base': '0.5rem',  // 8px
        'lg': '0.75rem',   // 12px
        'xl': '1rem',      // 16px
        'full': '9999px',
      },
      boxShadow: {
        'xs': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'sm': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'base': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'md': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'lg': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        'xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
      },
    },
  },
  plugins: [],
}
