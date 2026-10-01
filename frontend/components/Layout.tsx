"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function Layout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const links = [{ href: "/", label: "Profile" }, { href: "/contacts", label: "Contacts" }, { href: "/matches", label: "Matches" }, { href: "/outreach", label: "Outreach" }];
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
