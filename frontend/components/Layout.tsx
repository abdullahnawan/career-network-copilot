import Link from "next/link";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/95">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
          <Link href="/" className="text-lg font-semibold tracking-tight text-white">
            Career Network <span className="text-cyan-300">Copilot</span>
          </Link>
          <nav className="flex gap-4 text-sm text-slate-300" aria-label="Primary navigation">
            <Link href="/" className="hover:text-cyan-200">Profile</Link>
            <Link href="/contacts" className="hover:text-cyan-200">Contacts</Link>
            <Link href="/matches" className="hover:text-cyan-200">Matches</Link>
          </nav>
        </div>
      </header>
      <div className="mx-auto max-w-6xl px-5 py-10">{children}</div>
    </div>
  );
}
