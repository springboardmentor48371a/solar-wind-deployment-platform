import './globals.css'
import { AuthProvider } from '../lib/AuthContext'
import { ToastProvider } from '../lib/ToastContext'

export const metadata = {
  title: 'Solstice OS — Solar & Wind Deployment Intelligence',
  description:
    'Solar & Wind Deployment Intelligence Platform: physics-based and ML-assisted environmental, geographic, and infrastructure analysis for renewable energy site selection.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
