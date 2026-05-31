import { useState } from "react";
import { createAgent } from "../../services/api";
import { useAppStore } from "../../store";

const MODELS = [
  "gpt-4o-mini",
  "gpt-4o",
  "ollama/qwen2.5:7b",
  "claude-3-5-sonnet",
];

const NODE_BINDINGS = [
  { value: "", label: "None" },
  { value: "triage_agent", label: "triage_agent — chargeback graph" },
  { value: "resolution_agent", label: "resolution_agent — chargeback graph" },
  { value: "routing_agent", label: "routing_agent — routing graph" },
  { value: "risk_agent", label: "risk_agent — routing graph" },
  { value: "policy_agent", label: "policy_agent — routing graph" },
];

export default function NewAgentPage() {
  const { setActivePage } = useAppStore();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    name: "",
    role: "",
    system_prompt: "",
    model: "gpt-4o-mini",
    tools: "",
    channels: "web",
    schedules_mode: "on_demand",
    skills: "",
    interaction_rules: "",
    guardrails: "",
    max_steps: "8",
    max_cost_usd: "0.10",
    runtime_node_binding: "",
    memory_enabled: false,
  });

  const set = (k: string, v: string | boolean) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.name || !form.role || !form.system_prompt) {
      alert("Name, role and system prompt are required.");
      return;
    }
    setSaving(true);
    try {
      await createAgent({
        name: form.name,
        role: form.role,
        system_prompt: form.system_prompt,
        model: form.model,
        tools: form.tools.split(",").map((t) => t.trim()).filter(Boolean),
        channels: form.channels.split(",").map((c) => c.trim()).filter(Boolean),
        schedules: { mode: form.schedules_mode },
        memory: { type: "postgres_pgvector", enabled: form.memory_enabled },
        limits: { max_steps: parseInt(form.max_steps), max_cost_usd: parseFloat(form.max_cost_usd) },
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
        interaction_rules: form.interaction_rules.split(",").map((r) => r.trim()).filter(Boolean),
        guardrails: form.guardrails.split(",").map((g) => g.trim()).filter(Boolean),
        runtime_node_binding: form.runtime_node_binding || null,
      });
      setSaved(true);
      setTimeout(() => setActivePage("agents"), 1000);
    } catch (e) {
      alert("Failed to save agent.");
    } finally {
      setSaving(false);
    }
  };

  const inputStyle = {
    width: "100%", padding: "7px 10px",
    border: "1px solid var(--border2)", borderRadius: 6,
    fontSize: 12, background: "var(--bg2)", color: "var(--txt0)",
    fontFamily: "inherit", outline: "none",
  };

  const labelStyle = {
    fontSize: 11.5, color: "var(--txt1)", marginBottom: 4, fontWeight: 500, display: "block",
  };

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>New Agent</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>All fields are read by the LangGraph runtime — system_prompt, model, guardrails passed to the node on execution</p>
        </div>
      </div>

      <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div>
            <label style={labelStyle}>Agent name</label>
            <input style={inputStyle} placeholder="e.g. Fraud Inspector" value={form.name} onChange={(e) => set("name", e.target.value)} />
          </div>
          <div>
            <label style={labelStyle}>Role / persona</label>
            <input style={inputStyle} placeholder="e.g. Analyzes transactions for fraud" value={form.role} onChange={(e) => set("role", e.target.value)} />
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={labelStyle}>
            System prompt <span style={{ fontSize: 10, color: "var(--teal)" }}>↓ injected into LangGraph node at runtime</span>
          </label>
          <textarea
            style={{ ...inputStyle, height: 80, resize: "none", fontFamily: "monospace", fontSize: 11.5 }}
            placeholder="You are a fraud analysis agent. Score each transaction for risk between 0 and 1..."
            value={form.system_prompt}
            onChange={(e) => set("system_prompt", e.target.value)}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div>
            <label style={labelStyle}>AI model <span style={{ fontSize: 10, color: "var(--teal)" }}>↓ used at runtime</span></label>
            <select style={inputStyle} value={form.model} onChange={(e) => set("model", e.target.value)}>
              {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Schedule <span style={{ fontSize: 10, color: "var(--teal)" }}>↓ Celery beat triggers</span></label>
            <select style={inputStyle} value={form.schedules_mode} onChange={(e) => set("schedules_mode", e.target.value)}>
              <option value="on_demand">on_demand</option>
              <option value="always_on">always_on</option>
              <option value="daily">daily</option>
              <option value="hourly">hourly</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>Memory <span style={{ fontSize: 10, color: "var(--teal)" }}>↓ pgvector retrieval</span></label>
            <select style={inputStyle} value={form.memory_enabled ? "true" : "false"} onChange={(e) => set("memory_enabled", e.target.value === "true")}>
              <option value="false">None</option>
              <option value="true">Persistent (pgvector)</option>
            </select>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div>
            <label style={labelStyle}>Tools <span style={{ fontSize: 10, color: "var(--txt2)" }}>comma separated</span></label>
            <input style={inputStyle} placeholder="transaction_lookup, fraud_risk_scorer" value={form.tools} onChange={(e) => set("tools", e.target.value)} />
          </div>
          <div>
            <label style={labelStyle}>Channels <span style={{ fontSize: 10, color: "var(--txt2)" }}>comma separated</span></label>
            <input style={inputStyle} placeholder="web, slack" value={form.channels} onChange={(e) => set("channels", e.target.value)} />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div>
            <label style={labelStyle}>Interaction rules <span style={{ fontSize: 10, color: "var(--txt2)" }}>comma separated</span></label>
            <input style={inputStyle} placeholder="Always cite transaction ID" value={form.interaction_rules} onChange={(e) => set("interaction_rules", e.target.value)} />
          </div>
          <div>
            <label style={labelStyle}>Guardrails <span style={{ fontSize: 10, color: "var(--teal)" }}>↓ enforced in runtime node</span></label>
            <input style={inputStyle} placeholder="Never block without human confirmation" value={form.guardrails} onChange={(e) => set("guardrails", e.target.value)} />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div>
            <label style={labelStyle}>Skills <span style={{ fontSize: 10, color: "var(--txt2)" }}>comma separated</span></label>
            <input style={inputStyle} placeholder="fraud_analysis, payment_ops" value={form.skills} onChange={(e) => set("skills", e.target.value)} />
          </div>
          <div>
            <label style={labelStyle}>Limits</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input style={inputStyle} placeholder="max_steps: 8" value={form.max_steps} onChange={(e) => set("max_steps", e.target.value)} />
              <input style={inputStyle} placeholder="max_cost_usd: 0.10" value={form.max_cost_usd} onChange={(e) => set("max_cost_usd", e.target.value)} />
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={labelStyle}>
            Runtime node binding <span style={{ fontSize: 10, color: "var(--teal)" }}>↓ which graph node this agent powers</span>
          </label>
          <select style={inputStyle} value={form.runtime_node_binding} onChange={(e) => set("runtime_node_binding", e.target.value)}>
            {NODE_BINDINGS.map((b) => <option key={b.value} value={b.value}>{b.label}</option>)}
          </select>
          <div style={{ fontSize: 10.5, color: "var(--txt2)", marginTop: 3 }}>
            The runtime reads this agent's system_prompt, model, guardrails, and memory config when executing the bound node.
          </div>
        </div>

        <div style={{ height: 1, background: "var(--border)", margin: "14px 0" }} />

        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={handleSave}
            disabled={saving}
            style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600, opacity: saving ? 0.7 : 1 }}
          >
            {saved ? "✓ Saved!" : saving ? "Saving..." : "💾 Save Agent"}
          </button>
          <button
            onClick={() => setActivePage("workflow")}
            style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--border2)", background: "var(--bg2)", color: "var(--txt0)", cursor: "pointer" }}
          >
            🔀 Add to Workflow
          </button>
          <button
            onClick={() => setActivePage("agents")}
            style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--red)", background: "rgba(240,96,96,.12)", color: "var(--red)", cursor: "pointer" }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}