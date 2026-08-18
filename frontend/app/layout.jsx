import './globals.css'
import { AuthProvider } from '../lib/AuthContext'

export const metadata = {
  title: 'Solstice OS — Solar & Wind Deployment Intelligence',
  description:
    'AI-ready Solar & Wind Deployment Intelligence Platform: environmental, geographic, and infrastructure analysis for renewable energy site selection.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
