import { useEffect, useState } from "react";
import { getAgents, deleteAgent } from "../../services/api";
import { useAppStore } from "../../store";
import type { Agent } from "../../types";

const modelColor = (model: string) => {
  if (model.includes("gpt-4o")) return { bg: "rgba(77,142,247,.12)", color: "#4d8ef7" };
  if (model.includes("claude")) return { bg: "rgba(167,139,250,.12)", color: "#a78bfa" };
  if (model.includes("ollama")) return { bg: "rgba(78,203,130,.12)", color: "#4ecb82" };
  return { bg: "var(--bg3)", color: "var(--txt1)" };
};

const avatarColor = (name: string) => {
  const colors = [
    { bg: "rgba(77,142,247,.12)", color: "#4d8ef7" },
    { bg: "rgba(240,96,96,.12)", color: "#f06060" },
    { bg: "rgba(0,212,170,.10)", color: "#00d4aa" },
    { bg: "rgba(245,166,35,.12)", color: "#f5a623" },
    { bg: "rgba(167,139,250,.12)", color: "#a78bfa" },
  ];
  return colors[name.charCodeAt(0) % colors.length];
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const { setActivePage } = useAppStore();

  useEffect(() => {
    getAgents().then((data) => {
      setAgents(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this agent?")) return;
    await deleteAgent(id);
    setAgents((prev) => prev.filter((a) => a.id !== id));
  };

  if (loading) return (
    <div style={{ padding: 20, color: "var(--txt2)" }}>Loading agents...</div>
  );

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)", letterSpacing: "-.3px" }}>Agents</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>Each agent drives a node in the LangGraph runtime — config changes take effect on the next run</p>
        </div>
        <button
          onClick={() => setActivePage("create")}
          style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600 }}
        >
          + New Agent
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 18 }}>
        {[
          { label: "Active agents", value: agents.length, sub: "runtime-bound", up: true },
          { label: "Runs today", value: 0, sub: "via API or Slack", up: false },
          { label: "Tokens used", value: "0", sub: "Est. $0.00", up: false },
          { label: "Memory entries", value: 0, sub: "pgvector active", up: true },
        ].map((m) => (
          <div key={m.label} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px 14px" }}>
            <div style={{ fontSize: 10.5, color: "var(--txt2)", marginBottom: 4, fontWeight: 500 }}>{m.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--txt0)", fontFamily: "monospace" }}>{m.value}</div>
            <div style={{ fontSize: 10.5, color: m.up ? "var(--teal)" : "var(--txt2)", marginTop: 3 }}>{m.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
        Active agents — runtime-bound
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 18 }}>
        {agents.map((agent) => {
          const av = avatarColor(agent.name);
          const mc = modelColor(agent.model);
          const initials = agent.name.split(" ").map((w) => w[0]).slice(0, 2).join("");
          return (
            <div key={agent.id} style={{
              background: "var(--bg1)", border: "1px solid var(--teal)",
              boxShadow: "0 0 0 1px rgba(0,212,170,.18)",
              borderRadius: 12, padding: 14,
              display: "flex", flexDirection: "column", gap: 10,
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 36, height: 36, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, background: av.bg, color: av.color }}>
                    {initials}
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--txt0)" }}>{agent.name}</div>
                    <div style={{ fontSize: 11, color: "var(--txt2)" }}>{agent.role.slice(0, 40)}...</div>
                  </div>
                </div>
                <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(78,203,130,.12)", color: "var(--green)", fontWeight: 500 }}>
                  Active
                </span>
              </div>

              {agent.runtime_node_binding && (
                <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 10.5, color: "var(--teal)", background: "rgba(0,212,170,.10)", padding: "4px 8px", borderRadius: 4, border: "1px solid rgba(0,212,170,.2)" }}>
                  ⚡ Powers node: <strong>{agent.runtime_node_binding}</strong>
                </div>
              )}

              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {agent.tools.slice(0, 3).map((t) => (
                  <span key={t} style={{ fontSize: 10.5, padding: "2px 7px", borderRadius: 4, background: "var(--bg3)", color: "var(--txt1)", border: "1px solid var(--border)" }}>{t}</span>
                ))}
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", gap: 6 }}>
                  {agent.channels.includes("slack") && (
                    <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(77,142,247,.12)", color: "var(--blue)", fontWeight: 500 }}>Slack</span>
                  )}
                  <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: mc.bg, color: mc.color, fontWeight: 500 }}>{agent.model}</span>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button onClick={() => setActivePage("create")} style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--border2)", background: "var(--bg2)", color: "var(--txt0)", cursor: "pointer" }}>
                    Edit
                  </button>
                  <button onClick={() => handleDelete(agent.id)} style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--red)", background: "rgba(240,96,96,.12)", color: "var(--red)", cursor: "pointer" }}>
                    Delete
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
        Workflow templates
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {[
          { title: "Yuno Chargeback Management", desc: "Triage → Risk → Resolve → Approve. Agents + human approval gate.", color: "var(--blue)", bg: "rgba(77,142,247,.12)", icon: "🛡️", key: "yuno-chargeback-management" },
          { title: "Yuno Smart Payment Routing", desc: "Route → Risk → Policy → Recommend. Conditional routing based on provider health.", color: "var(--teal)", bg: "rgba(0,212,170,.10)", icon: "🔀", key: "yuno-smart-routing" },
        ].map((t) => (
          <div key={t.key} onClick={() => setActivePage("workflow")} style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: 14, cursor: "pointer", transition: "border-color .12s" }}
            onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "var(--teal)"}
            onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)"}
          >
            <div style={{ fontSize: 20, marginBottom: 6 }}>{t.icon}</div>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 3 }}>{t.title}</div>
            <div style={{ fontSize: 11, color: "var(--txt2)", marginBottom: 10 }}>{t.desc}</div>
            <div style={{ display: "flex", gap: 6 }}>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(0,212,170,.18)", color: "var(--teal)", fontWeight: 500 }}>Built-in</span>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "var(--bg3)", color: "var(--txt1)", fontWeight: 500 }}>Active</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}