"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../../components/AuthProvider";
import { formatApiError } from "../../lib/api";

export default function RegisterPage() {
  const { register } = useAuth(); const router = useRouter();
  const [name, setName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [confirmation, setConfirmation] = useState(""); const [error, setError] = useState("");
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); if (password.length < 10) { setError("Use at least 10 characters."); return; } if (password !== confirmation) { setError("Passwords do not match."); return; } try { await register(email, password, name); router.push("/"); } catch (e) { setError(formatApiError(e, "Unable to create your account.")); } }
  return <main className="mx-auto flex min-h-screen max-w-md items-center px-6"><section className="surface w-full card-accent-cobalt"><p className="eyebrow">Start thoughtfully</p><h1 className="page-title">Create your account.</h1><form onSubmit={submit} className="mt-8 space-y-4"><label className="form-label" htmlFor="display-name">Display name</label><input id="display-name" className="form-control w-full rounded-lg px-3 py-2" value={name} onChange={e => setName(e.target.value)} required /><label className="form-label" htmlFor="register-email">Email</label><input id="register-email" className="form-control w-full rounded-lg px-3 py-2" type="email" value={email} onChange={e => setEmail(e.target.value)} required /><label className="form-label" htmlFor="register-password">Password</label><input id="register-password" className="form-control w-full rounded-lg px-3 py-2" type="password" minLength={10} value={password} onChange={e => setPassword(e.target.value)} required /><label className="form-label" htmlFor="password-confirmation">Confirm password</label><input id="password-confirmation" className="form-control w-full rounded-lg px-3 py-2" type="password" minLength={10} value={confirmation} onChange={e => setConfirmation(e.target.value)} required />{error && <p role="alert" className="field-error">{error}</p>}<button className="ui-button ui-button-primary w-full" type="submit">Create account</button></form><p className="mt-6 text-sm text-slate-400">Already registered? <Link className="text-cyan-300 hover:underline" href="/login">Sign in</Link></p></section></main>;
}
