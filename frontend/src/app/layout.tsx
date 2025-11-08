import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PayOffOrInvest - Should You Pay Off Your Mortgage?',
  description: 'Get a data-backed answer using 100 years of market returns',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
