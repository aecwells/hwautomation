module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'prettier'
  ],
  globals: {
    bootstrap: 'readonly',
    io: 'readonly'
  },
  overrides: [
    {
      env: {
        node: true
      },
      files: [
        '.eslintrc.{js,cjs}'
      ],
      parserOptions: {
        sourceType: 'script'
      }
    }
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  plugins: [
    'prettier'
  ],
  rules: {
    'prettier/prettier': 'error',
    'no-unused-vars': 'warn',
    'no-console': 'off' // Allow console statements in development
  },
  // Ignore node_modules and dist directories
  ignorePatterns: [
    'node_modules/',
    'src/hwautomation/web/static/dist/',
    '*.min.js'
  ]
};
