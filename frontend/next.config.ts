import type { NextConfig } from 'next'
// 'standalone' makes `next build` emit .next/standalone (a self-contained server.js) for the Docker image.
const config: NextConfig = { reactStrictMode: true, output: 'standalone' }
export default config
