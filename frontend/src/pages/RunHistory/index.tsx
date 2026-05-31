import { useEffect, useState } from "react";
import { getRuns } from "../../services/api";
import { useAppStore } from "../../store";
import type { WorkflowRun } from "../../types";

const statusBadge = (status: string) => {
  switch (status) {
    case "completed": return { bg: "rgba(78,203,130,.12)", color: "var(--green)", label: "Completed" };
    case "running": return { bg: "rgba(0,212,170,.10)", color: "var(--teal)", label: "Running" };
    case "awaiting_approval": return { bg: "rgba(245,166,35,.12)", color: "var(--amber)", label: "Awaiting Approval" };
    case "failed": return { bg: "rgba(240,96,96,.12)", color: "var(--red)", label: "Failed" };
    case "queued": return { bg: "var(--bg3)", color: "var(--txt1)", label: "Queued" };
    default: return { bg: "var(--bg3)", color: "var(--txt1)", label: status };
  }
};

const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
};

export default function RunHistoryPage() {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const { setActivePage, setActiveRunId } = useAppStore();

  useEffect(() => {
    getRuns(50).then((data) => {
      setRuns(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const completed = runs.filter((r) => r.status === "completed").length;
  const awaiting = runs.filter((r) => r.status === "awaiting_approval").length;
  const failed = runs.filter((r) => r.status === "failed").length;

  const handleViewRun = (run: WorkflowRun) => {
    setActiveRunId(run.id);
    setActivePage("monitor");
  };

  if (loading) return <div style={{ padding: 20, color: "var(--txt2)" }}>Loading runs...</div>;

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>Run History</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>All workflow runs · click Live to open monitor for any run</p>
        </div>
        <button
          onClick={() => setActivePage("workflow")}
          style={{ fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600 }}
        >
          ▶ New Run
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 18 }}>
        {[
          { label: "Total runs", value: runs.length, color: "var(--txt0)" },
          { label: "Completed", value: completed, color: "var(--green)" },
          { label: "Awaiting approval", value: awaiting, color: "var(--amber)" },
          { label: "Failed", value: failed, color: "var(--red)" },
        ].map((m) => (
          <div key={m.label} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px 14px" }}>
            <div style={{ fontSize: 10.5, color: "var(--txt2)", marginBottom: 4 }}>{m.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: m.color, fontFamily: "monospace" }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: "10px 14px" }}>
        {runs.length === 0 && (
          <div style={{ fontSize: 11, color: "var(--txt2)", textAlign: "center", padding: 20 }}>
            No runs yet. Start a workflow to see history.
          </div>
        )}
        {runs.map((run) => {
          const badge = statusBadge(run.status);
          return (
            <div key={run.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 0", borderBottom: "1px solid var(--border)" }}>
              <span style={{ fontFamily: "monospace", fontSize: 10.5, color: "var(--txt2)", width: 80, flexShrink: 0 }}>
                {run.id.slice(0, 8)}
              </span>
              <span style={{ flex: 1, fontSize: 12, fontWeight: 500, color: "var(--txt0)" }}>
                {run.template_key}
              </span>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: badge.bg, color: badge.color, fontWeight: 500, flexShrink: 0 }}>
                {badge.label}
              </span>
              <span style={{ fontSize: 11, color: "var(--txt2)", width: 60, textAlign: "center", flexShrink: 0 }}>
                {run.channel === "slack" ? (
                  <span style={{ fontSize: 10.5, padding: "2px 6px", borderRadius: 20, background: "rgba(77,142,247,.12)", color: "var(--blue)" }}>Slack</span>
                ) : run.channel}
              </span>
              <span style={{ fontSize: 10.5, color: "var(--txt2)", width: 58, textAlign: "right", fontFamily: "monospace", flexShrink: 0 }}>
                {timeAgo(run.created_at)}
              </span>
              <button
                onClick={() => handleViewRun(run)}
                style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--border2)", background: "var(--bg2)", color: "var(--txt0)", cursor: "pointer", flexShrink: 0 }}
              >
                {run.status === "running" ? "👁 Live" : "👁 Replay"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}