"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import { formatApiError } from "../../lib/api";

export default function LoginPage() {
  const { login } = useAuth(); const router = useRouter();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); try { await login(email, password); router.push("/"); } catch (e) { setError(formatApiError(e, "Unable to sign in. Check your email and password.")); } }
  return <main className="mx-auto flex min-h-screen max-w-md items-center px-6"><section className="surface w-full card-accent-cobalt"><p className="eyebrow">Welcome back</p><h1 className="page-title">Sign in to your workspace.</h1>
    <form onSubmit={submit} className="mt-8 space-y-4"><label className="block text-sm text-slate-300">Email<input className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label><label className="block text-sm text-slate-300">Password<input className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" type="password" value={password} onChange={e => setPassword(e.target.value)} required /></label>{error && <p role="alert" className="text-sm text-rose-300">{error}</p>}<button className="ui-button ui-button-primary w-full" type="submit">Sign in</button></form>
    <p className="mt-6 text-sm text-slate-400">New here? <Link className="text-cyan-300 hover:underline" href="/register">Create an account</Link></p></section></main>;
}
