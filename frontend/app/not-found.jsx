'use client'

import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(1000px_500px_at_15%_-10%,#eaf5ee_0%,transparent_55%),radial-gradient(900px_500px_at_100%_110%,#e4f2ea_0%,transparent_55%)] bg-bg">
      <div className="text-center max-w-[420px]">
        <div className="w-[64px] h-[64px] rounded-2xl bg-gradient-to-br from-[#3fae7c] to-brand flex items-center justify-center text-3xl shadow mx-auto mb-5">🧭</div>
        <h1 className="text-2xl mb-2">This page doesn't exist</h1>
        <p className="text-ink-muted text-[14.5px] mb-6">
          The link might be broken, or the page may have moved. Let's get you back to somewhere useful.
        </p>
        <div className="flex gap-2.5 justify-center flex-wrap">
          <Link href="/dashboard"><button className="btn">Go to Dashboard</button></Link>
          <Link href="/"><button className="btn-secondary">Back to Home</button></Link>
        </div>
      </div>
    </div>
  )
}
