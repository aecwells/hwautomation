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
        // Main application JS
        app: resolve(__dirname, 'src/hwautomation/web/assets/js/app.js'),
        dashboard: resolve(__dirname, 'src/hwautomation/web/assets/js/pages/dashboard.js'),
        firmware: resolve(__dirname, 'src/hwautomation/web/assets/js/pages/firmware.js'),
        database: resolve(__dirname, 'src/hwautomation/web/assets/js/pages/database.js'),

        // Main application CSS
        main: resolve(__dirname, 'src/hwautomation/web/assets/scss/main.scss'),
        dashboard_styles: resolve(__dirname, 'src/hwautomation/web/assets/scss/pages/dashboard.scss'),
        firmware_styles: resolve(__dirname, 'src/hwautomation/web/assets/scss/pages/firmware.scss'),
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
    terserOptions: {
      compress: {
        drop_console: false, // Keep console.log in development
        drop_debugger: true
      }
    }
  },

  // CSS configuration
  css: {
    preprocessorOptions: {
      scss: {
        // Additional SCSS options
        additionalData: `@import "src/hwautomation/web/assets/scss/variables.scss";`
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
      '@': resolve(__dirname, 'src/hwautomation/web/assets'),
      '@js': resolve(__dirname, 'src/hwautomation/web/assets/js'),
      '@scss': resolve(__dirname, 'src/hwautomation/web/assets/scss'),
      '@components': resolve(__dirname, 'src/hwautomation/web/assets/js/components')
    }
  },

  // Environment variables
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString())
  }
});
