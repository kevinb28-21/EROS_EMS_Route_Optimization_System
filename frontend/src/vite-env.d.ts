/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend origin only (no path). Example: https://eros-api.up.railway.app */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
