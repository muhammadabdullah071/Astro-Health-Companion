import type { Metadata, Viewport } from 'next'
import './globals.css'
import { AppProvider } from '@/components/AppProvider'
import Shell from '@/components/Shell'
import SwRegister from '@/components/SwRegister'

export const metadata: Metadata = {
  title: 'Astro-Health Companion',
  description: 'Offline-first health awareness for crews beyond Earth’s reach. All demo data is simulated.',
  manifest: '/manifest.webmanifest',
  icons: { icon: '/icon.svg' },
}
export const viewport: Viewport = { width: 'device-width', initialScale: 1, viewportFit: 'cover', themeColor: '#050E2B' }

const themeInit = `try{var t=localStorage.getItem('ahc-theme');document.documentElement.setAttribute('data-theme',t==='light'||t==='dark'?t:'dark')}catch(e){document.documentElement.setAttribute('data-theme','dark')}`

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Fira+Sans:wght@500;600;700;900&family=Overpass:wght@400;600;700&display=swap" rel="stylesheet" />
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body>
        <AppProvider><Shell>{children}</Shell></AppProvider>
        <SwRegister />
      </body>
    </html>
  )
}
