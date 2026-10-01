export function StatusMessage({
  kind,
  children,
}: {
  kind: "error" | "success" | "info";
  children: React.ReactNode;
}) {
  const styles = {
    error: "status-error",
    success: "status-success",
    info: "status-info",
  };
  return (
    <div aria-live="polite" role={kind === "error" ? "alert" : "status"} className={`status-message ${styles[kind]}`}>
      {children}
    </div>
  );
}
