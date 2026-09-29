export function StatusMessage({
  kind,
  children,
}: {
  kind: "error" | "success" | "info";
  children: React.ReactNode;
}) {
  const styles = {
    error: "border-rose-400/30 bg-rose-400/10 text-rose-100",
    success: "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
    info: "border-cyan-400/30 bg-cyan-400/10 text-cyan-100",
  };
  return (
    <div role={kind === "error" ? "alert" : "status"} className={`rounded-xl border px-4 py-3 text-sm ${styles[kind]}`}>
      {children}
    </div>
  );
}
