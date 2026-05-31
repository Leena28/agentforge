import { useAppStore } from "../store";

export default function Topbar() {
  const { activePage } = useAppStore();

  const titles: Record<string, string> = {
    agents: "Agents",
    create: "New Agent",
    workflow: "Workflow Builder",
    templates: "Templates",
    monitor: "Live Monitor",
    runs: "Run History",
    scheduler: "Scheduler",
    memory: "Memory / pgvector",
    channels: "Channel Management",
  };

  return (
    <div style={{
      height: 48,
      background: "var(--bg1)",
      borderBottom: "1px solid var(--border)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 16px",
      flexShrink: 0,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9, fontWeight: 700, fontSize: 15, color: "var(--txt0)" }}>
        <div style={{
          width: 28, height: 28,
          background: "var(--teal)",
          borderRadius: 6,
          display: "flex", alignItems: "center", justifyContent: "center",
          color: "#000", fontWeight: 700, fontSize: 13,
        }}>
          AF
        </div>
        AgentForge
        <span style={{ fontSize: 11, color: "var(--txt2)", fontWeight: 400 }}>
          — {titles[activePage] || ""}
        </span>
      </div>
      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <span style={{
          fontSize: 11, padding: "3px 9px", borderRadius: 20,
          border: "1px solid var(--teal)", color: "var(--teal)",
          background: "rgba(0,212,170,.10)",
          display: "inline-flex", alignItems: "center", gap: 4,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: "50%",
            background: "var(--teal)",
            animation: "pulse 1.8s infinite",
            display: "inline-block",
          }} />
          SSE live
        </span>
        <span style={{
          fontSize: 11, padding: "3px 9px", borderRadius: 20,
          border: "1px solid var(--border2)", color: "var(--txt1)",
          background: "var(--bg2)",
          display: "inline-flex", alignItems: "center", gap: 4,
        }}>
          pgvector active
        </span>
      </div>
    </div>
  );
}