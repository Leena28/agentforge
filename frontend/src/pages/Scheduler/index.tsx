import { useEffect, useState } from "react";
import { getAgents } from "../../services/api";
import type { Agent } from "../../types";

export default function SchedulerPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAgents().then((data) => {
      setAgents(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const getScheduleMode = (agent: Agent) => {
    const s = agent.schedules as Record<string, string>;
    return s?.mode || "on_demand";
  };

  const getScheduleNext = (mode: string) => {
    switch (mode) {
      case "always_on": return "Polling queue every 30s";
      case "daily": return "Next run: tomorrow 09:00 UTC";
      case "hourly": return "Next run: top of next hour";
      case "on_event": return "Triggered when Slack message received or run created via API";
      default: return "Only runs when explicitly triggered by another agent or API call";
    }
  };

  const scheduledCount = agents.filter((a) => getScheduleMode(a) !== "on_demand").length;

  if (loading) return <div style={{ padding: 20, color: "var(--txt2)" }}>Loading scheduler...</div>;

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>Scheduler</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>Celery Beat — triggers runs automatically based on each agent's schedule config</p>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(78,203,130,.12)", color: "var(--green)", display: "inline-flex", alignItems: "center", gap: 4 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />
            Celery Beat configured
          </span>
          <button style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--border2)", background: "var(--bg2)", color: "var(--txt0)", cursor: "pointer" }}>
            🔄 Refresh
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 18 }}>
        {[
          { label: "Scheduled agents", value: agents.length, sub: `${scheduledCount} active triggers`, up: true },
          { label: "Triggered today", value: 0, sub: "via Celery Beat", up: false },
          { label: "Next trigger", value: "—", sub: "check agent config", up: false },
          { label: "Beat status", value: "OK", sub: "configured at startup", up: true, teal: true },
        ].map((m) => (
          <div key={m.label} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px 14px" }}>
            <div style={{ fontSize: 10.5, color: "var(--txt2)", marginBottom: 4 }}>{m.label}</div>
            <div style={{ fontSize: m.value === "OK" ? 16 : 24, fontWeight: 700, color: m.teal ? "var(--teal)" : "var(--txt0)", fontFamily: "monospace" }}>{m.value}</div>
            <div style={{ fontSize: 10.5, color: m.up ? "var(--teal)" : "var(--txt2)", marginTop: 3 }}>{m.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
        Agent schedules
      </div>
      <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: "10px 14px", marginBottom: 16 }}>
        {agents.map((agent) => {
          const mode = getScheduleMode(agent);
          const next = getScheduleNext(mode);
          const isActive = mode !== "on_demand";
          return (
            <div key={agent.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
              <div style={{ fontWeight: 600, fontSize: 12.5, color: "var(--txt0)", width: 160, flexShrink: 0 }}>{agent.name}</div>
              <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--blue)", width: 120, flexShrink: 0 }}>{mode}</div>
              <div style={{ fontSize: 11, color: "var(--txt2)", flex: 1, fontFamily: "monospace" }}>{next}</div>
              <div
                style={{
                  width: 32, height: 18, borderRadius: 9,
                  background: isActive ? "var(--teal)" : "var(--bg3)",
                  border: `1px solid ${isActive ? "var(--teal)" : "var(--border2)"}`,
                  position: "relative", cursor: "pointer", flexShrink: 0,
                }}
              >
                <div style={{
                  position: "absolute", width: 12, height: 12,
                  borderRadius: "50%", background: "#fff",
                  top: 2, left: isActive ? 16 : 2,
                  transition: "left .15s",
                }} />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
        How scheduling works
      </div>
      <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
        <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--teal)", lineHeight: 1.9 }}>
          1. Agent.schedules field stores mode, cron, hour, minute config<br />
          2. scheduler/beat.py reads all agents from DB on startup<br />
          3. Builds Celery Beat schedule using crontab() for each agent<br />
          4. execute_scheduled_workflow_task fires at configured time<br />
          5. Creates a new WorkflowRun with channel="scheduler"<br />
          6. Result delivered via Slack if agent has slack channel
        </div>
      </div>
    </div>
  );
}