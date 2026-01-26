/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // EROS color palette - "Command Center" theme
        // Dark, professional with emergency accent colors
        eros: {
          // Primary backgrounds
          dark: '#0a0f1a',
          darker: '#060912',
          card: '#111827',
          'card-hover': '#1f2937',
          
          // Text
          text: '#f8fafc',
          'text-muted': '#94a3b8',
          'text-dim': '#64748b',
          
          // Accent colors
          primary: '#3b82f6',      // Blue - primary actions
          'primary-dim': '#1d4ed8',
          
          // Status colors
          critical: '#ef4444',     // Red - critical severity
          'critical-dim': '#991b1b',
          major: '#f59e0b',        // Amber - major severity
          'major-dim': '#b45309',
          minor: '#22c55e',        // Green - minor severity
          'minor-dim': '#166534',
          
          // Vehicle status colors
          available: '#22c55e',
          dispatched: '#3b82f6',
          'on-scene': '#f59e0b',
          transporting: '#8b5cf6',
          
          // Hospital status
          open: '#22c55e',
          diversion: '#f59e0b',
          closed: '#ef4444',
          
          // UI elements
          border: '#1e293b',
          'border-active': '#3b82f6',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      boxShadow: {
        'glow-critical': '0 0 20px rgba(239, 68, 68, 0.3)',
        'glow-primary': '0 0 20px rgba(59, 130, 246, 0.3)',
      }
    },
  },
  plugins: [],
}
