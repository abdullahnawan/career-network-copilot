"use client";

import { useEffect, useRef, useState } from "react";

export function Button({ variant = "primary", className = "", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger" }) {
  return <button {...props} className={`ui-button ui-button-${variant} ${className}`} />;
}

export function Surface({ children, className = "", as: Tag = "section" }: { children: React.ReactNode; className?: string; as?: "section" | "div" | "article" }) {
  return <Tag className={`surface ${className}`}>{children}</Tag>;
}

export function PageHeader({ eyebrow, title, description }: { eyebrow?: string; title: string; description?: string }) {
  return <header className="page-header">{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="page-description">{description}</p>}</header>;
}

export function SectionHeader({ title, description, accent = "cobalt" }: { title: string; description?: string; accent?: "cobalt" | "coral" | "yellow" }) {
  return <div className={`section-header section-header-${accent}`}><div className="section-header-marker" aria-hidden="true" /><div><h2>{title}</h2>{description && <p>{description}</p>}</div></div>;
}

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "success" | "warning" | "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function MetadataLabel({ children }: { children: React.ReactNode }) {
  return <span className="metadata-label">{children}</span>;
}

export function DataValue({ children }: { children: React.ReactNode }) {
  return <span className="data-value">{children}</span>;
}

export function FieldGroup({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return <fieldset className="field-group"><legend>{title}</legend>{description && <p className="field-group-description">{description}</p>}<div className="field-group-content">{children}</div></fieldset>;
}

export function Score({ value }: { value: number }) {
  return <div className="score-block"><div><strong className="score-value tabular-nums">{value}%</strong><span className="score-total">/100</span></div><div className="score-meter" aria-label={`${value} out of 100`}><span style={{ width: `${Math.max(0, Math.min(value, 100))}%` }} /></div></div>;
}

export function EmptyState({ title, children, action }: { title: string; children?: React.ReactNode; action?: React.ReactNode }) {
  return <div className="empty-state"><h2>{title}</h2>{children && <p>{children}</p>}{action && <div className="empty-state-action">{action}</div>}</div>;
}

export function ConfirmDialog({ open, title, description, confirmLabel = "Confirm", onConfirm, onCancel }: { open: boolean; title: string; description: string; confirmLabel?: string; onConfirm: () => void; onCancel: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { const dialog = ref.current; if (!dialog) return; if (open && !dialog.open) { if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", ""); } if (!open && dialog.open) dialog.close(); }, [open]);
  return <dialog ref={ref} className="confirm-dialog" onCancel={onCancel}><h2>{title}</h2><p>{description}</p><div className="dialog-actions"><Button variant="secondary" type="button" onClick={onCancel}>Cancel</Button><Button type="button" onClick={onConfirm}>{confirmLabel}</Button></div></dialog>;
}

export function useConfirmation() {
  const [request, setRequest] = useState<{ title: string; description: string; confirmLabel?: string; resolve: (value: boolean) => void } | null>(null);
  const confirm = (title: string, description: string, confirmLabel?: string) => new Promise<boolean>((resolve) => setRequest({ title, description, confirmLabel, resolve }));
  const dialog = <ConfirmDialog open={Boolean(request)} title={request?.title ?? ""} description={request?.description ?? ""} confirmLabel={request?.confirmLabel} onCancel={() => { request?.resolve(false); setRequest(null); }} onConfirm={() => { request?.resolve(true); setRequest(null); }} />;
  return { confirm, dialog };
}
