// Run from this directory: pm2 start ecosystem.config.js
// Frontend runs the same CRACO development server as `npm start`.
// Restart the frontend after changing frontend/.env. Backend uses .env.mysql.
const path = require('node:path');

const FRONTEND_PORT = 4000;
const BACKEND_PORT = 4001;
const backend = path.join(__dirname, 'backend');
const frontend = path.join(__dirname, 'frontend');
const python = path.join(backend, '.venv_backend', process.platform === 'win32' ? 'Scripts' : 'bin',
  process.platform === 'win32' ? 'python.exe' : 'python');

const defaults = {
  exec_mode: 'fork',
  instances: 1,
  autorestart: true,
  watch: false,
  min_uptime: '5s',
  max_restarts: 10,
  restart_delay: 3000,
  kill_timeout: 10000,
  windowsHide: true,
  time: true,
};

module.exports = {
  apps: [
    {
      ...defaults,
      name: 'meow-backend',
      cwd: backend,
      script: python,
      interpreter: 'none',
      args: ['-m', 'uvicorn', 'server:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT), '--workers', '1'],
      env: { PYTHONUNBUFFERED: '1' },
    },
    {
      ...defaults,
      name: 'meow-frontend',
      cwd: frontend,
      script: path.join(frontend, 'scripts', 'start-pm2.cjs'),
      interpreter: process.execPath,
      env: {
        NODE_ENV: 'development',
        BABEL_ENV: 'development',
        HOST: '0.0.0.0',
        PORT: String(FRONTEND_PORT),
        BROWSER: 'none',
      },
    },
  ],
};
