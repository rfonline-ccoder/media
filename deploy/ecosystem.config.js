// PM2 Ecosystem configuration for SwagMedia
module.exports = {
  apps: [
    {
      name: 'swagmedia-backend',
      cwd: '/var/www/swagmedia/backend',
      script: 'python',
      args: '-m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4',
      interpreter: 'python3',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/var/www/swagmedia/backend'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/pm2/swagmedia-backend-error.log',
      out_file: '/var/log/pm2/swagmedia-backend-out.log',
      log_file: '/var/log/pm2/swagmedia-backend-combined.log',
      time: true,
      min_uptime: '10s',
      max_restarts: 10
    }
  ]
};