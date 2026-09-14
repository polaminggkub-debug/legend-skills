import tseslint from 'typescript-eslint';

export default [
  {
    files: ['fixtures/imports/*.js'],
    linterOptions: { noInlineConfig: true },
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: ['@app/db', '@app/db/**'],
          message: 'UI uses @app/application/orders; keep database access inside the service.',
        }],
      }],
    },
  },
  {
    files: ['fixtures/async/*.ts'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: './tsconfig.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: { '@typescript-eslint': tseslint.plugin },
    rules: {
      '@typescript-eslint/no-floating-promises': ['error', { ignoreVoid: false }],
    },
  },
];
