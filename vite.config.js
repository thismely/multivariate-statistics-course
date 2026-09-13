import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({base:'./',define:{__LOCAL_SOURCES__:'false'},plugins:[vue()],build:{rollupOptions:{output:{manualChunks:{three:['three'],vue:['vue','pinia']}}}}})
