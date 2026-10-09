"use client";
/* eslint-disable @next/next/no-location-assign-relative-destination */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "./AuthProvider";

export function Layout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { user, loading, logout } = useAuth();
  useEffect(() => { if (!loading && !user) window.location.assign("/login"); }, [loading, user]);
  // Render nothing protected until the session is confirmed, so signed-out visitors never see the app shell.
  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500" role="status">
        {loading ? "Checking your session…" : "Redirecting to sign in…"}
      </div>
    );
  }
  const links = [{ href: "/", label: "Profile" }, { href: "/contacts", label: "Contacts" }, { href: "/matches", label: "Matches" }, { href: "/outreach", label: "Outreach" }, { href: "/applications", label: "Applications" }];
  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <Link href="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark">CN</span><span>Career Network<strong>Copilot</strong></span>
        </Link>
        <nav aria-label="Primary navigation">
          {links.map((link) => <Link key={link.href} href={link.href} onClick={() => setOpen(false)} className={pathname === link.href ? "nav-link active" : "nav-link"} aria-current={pathname === link.href ? "page" : undefined}>{link.label}</Link>)}
        </nav>
        <p className="sidebar-note">A calm workspace for thoughtful career conversations.</p>
        {user && <div className="mt-auto border-t border-slate-800 pt-4 text-sm text-slate-400">
          <Link href="/account" className="block truncate hover:text-white">{user.display_name || user.email}</Link>
          <button type="button" className="mt-2 text-xs hover:text-white" onClick={async () => { await logout(); window.location.assign("/login"); }}>Log out</button>
        </div>}
      </aside>
      <div className="main-shell">
        <header className="mobile-header">
          <Link href="/" className="brand"><span className="brand-mark">CN</span><span>Career Network<strong>Copilot</strong></span></Link>
          <button className="menu-button" type="button" aria-label="Open navigation" aria-expanded={open} onClick={() => setOpen(!open)}>☰</button>
        </header>
        <main className="content-shell">{children}</main>
      </div>
    </div>
  );
}
