import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  // Base path for assets
  base: '/static/',

  // Build configuration
  build: {
    // Output directory relative to project root
    outDir: 'src/hwautomation/web/static/dist',

    // Generate manifest for Flask integration
    manifest: true,

    // Rollup options
    rollupOptions: {
      input: {
        // Core modular frontend
        app: resolve(__dirname, 'src/hwautomation/web/frontend/js/core/app.js'),
        'module-loader': resolve(__dirname, 'src/hwautomation/web/frontend/js/core/module-loader.js'),

        // Services
        'services/api': resolve(__dirname, 'src/hwautomation/web/frontend/js/services/api.js'),
        'services/state': resolve(__dirname, 'src/hwautomation/web/frontend/js/services/state.js'),
        'services/notifications': resolve(__dirname, 'src/hwautomation/web/frontend/js/services/notifications.js'),

        // Components
        'components/theme-manager': resolve(__dirname, 'src/hwautomation/web/frontend/js/components/theme-manager.js'),
        'components/connection-status': resolve(__dirname, 'src/hwautomation/web/frontend/js/components/connection-status.js'),
        'components/device-selection': resolve(__dirname, 'src/hwautomation/web/frontend/js/components/device-selection.js'),

        // Utils
        'utils/dom': resolve(__dirname, 'src/hwautomation/web/frontend/js/utils/dom.js'),
        'utils/format': resolve(__dirname, 'src/hwautomation/web/frontend/js/utils/format.js'),

        // Main application CSS
        main: resolve(__dirname, 'src/hwautomation/web/frontend/css/main.css'),
      },
      output: {
        // Naming pattern for built files
        entryFileNames: 'js/[name].[hash].js',
        chunkFileNames: 'js/[name].[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(css)$/.test(assetInfo.name)) {
            return `css/[name].[hash].${ext}`;
          }
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
            return `images/[name].[hash].${ext}`;
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
            return `fonts/[name].[hash].${ext}`;
          }
          return `assets/[name].[hash].${ext}`;
        }
      }
    },

    // Clean dist directory
    emptyOutDir: true,

    // Source maps for debugging
    sourcemap: true,

    // Minification
    minify: 'terser',
  },

  // CSS configuration
  css: {
    preprocessorOptions: {
      scss: {
        // Additional SCSS options can be added here
      }
    },
    postcss: {
      plugins: [
        require('autoprefixer'),
        require('cssnano')({
          preset: 'default'
        })
      ]
    }
  },

  // Server configuration for development
  server: {
    host: '0.0.0.0',
    port: 3000,
    cors: true,
    // Proxy API calls to Flask during development
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/socket.io': {
        target: 'ws://localhost:5000',
        ws: true
      }
    }
  },

  // Preview server configuration
  preview: {
    host: '0.0.0.0',
    port: 3001
  },

  // Plugin configuration
  plugins: [],

  // Resolve configuration
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src/hwautomation/web/frontend'),
      '@js': resolve(__dirname, 'src/hwautomation/web/frontend/js'),
      '@css': resolve(__dirname, 'src/hwautomation/web/frontend/css'),
      '@components': resolve(__dirname, 'src/hwautomation/web/frontend/js/components')
    }
  },

  // Environment variables
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString())
  }
});
