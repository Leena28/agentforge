import { useEffect, useState } from "react";
import { getAgents } from "../../services/api";
import type { Agent } from "../../types";

export default function MemoryPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("");
  const [query, setQuery] = useState("duplicate charge high amount");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAgents().then((data) => {
      setAgents(data);
      if (data.length > 0) setSelectedAgent(data[0].id);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const inputStyle = {
    width: "100%", padding: "7px 10px",
    border: "1px solid var(--border2)", borderRadius: 6,
    fontSize: 12, background: "var(--bg2)", color: "var(--txt0)",
    fontFamily: "inherit", outline: "none",
  };

  if (loading) return <div style={{ padding: 20, color: "var(--txt2)" }}>Loading memory...</div>;

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>Memory / pgvector</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>Persistent agent memory — embeddings stored in PostgreSQL pgvector · retrieved via similarity search at runtime</p>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(0,212,170,.10)", color: "var(--teal)", display: "inline-flex", alignItems: "center", gap: 4 }}>
            🗄️ pgvector:pg16
          </span>
          <button style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--red)", background: "rgba(240,96,96,.12)", color: "var(--red)", cursor: "pointer" }}>
            🗑️ Clear Agent Memory
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 18 }}>
        {[
          { label: "Total embeddings", value: 0, sub: "pgvector active", up: true },
          { label: "Avg retrieval time", value: "—", sub: "similarity search", up: false },
          { label: "Similarity threshold", value: "0.82", sub: "configurable", up: false },
          { label: "Agents using memory", value: agents.filter((a) => (a.memory as Record<string, unknown>)?.enabled).length, sub: "pgvector enabled", up: false },
        ].map((m) => (
          <div key={m.label} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px 14px" }}>
            <div style={{ fontSize: 10.5, color: "var(--txt2)", marginBottom: 4 }}>{m.label}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--txt0)", fontFamily: "monospace" }}>{m.value}</div>
            <div style={{ fontSize: 10.5, color: m.up ? "var(--teal)" : "var(--txt2)", marginTop: 3 }}>{m.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
            Recent memory writes
          </div>
          <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: "10px 12px" }}>
            <div style={{ fontSize: 11, color: "var(--txt2)", textAlign: "center", padding: 20 }}>
              Memory entries are written when PGVECTOR_ENABLED=true and OPENAI_API_KEY is configured.
              Currently running in demo mode without embeddings.
            </div>
            {[
              { writer: "Resolution Agent · run_a3f2", content: "TXN-4821 chargeback approved · risk 0.67 · resolved via standard process", time: "just now", dim: "1536-dim" },
              { writer: "Chargeback Triage Agent · run_b7c1", content: "Pattern: Rappi Brazil BRL 350 → low risk → standard representment", time: "8m ago", dim: "1536-dim" },
            ].map((m, i) => (
              <div key={i} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", marginBottom: 8 }}>
                <div style={{ fontSize: 11.5, color: "var(--txt1)", marginBottom: 4 }}>Written by: {m.writer}</div>
                <div style={{ fontSize: 12, color: "var(--txt0)", lineHeight: 1.5, fontFamily: "monospace" }}>{m.content}</div>
                <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                  <span style={{ fontSize: 9.5, padding: "2px 8px", borderRadius: 20, background: "rgba(167,139,250,.12)", color: "var(--purple)" }}>{m.dim}</span>
                  <span style={{ fontSize: 9.5, padding: "2px 8px", borderRadius: 20, background: "var(--bg3)", color: "var(--txt1)" }}>{m.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
            Test similarity search
          </div>
          <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ fontSize: 11.5, color: "var(--txt1)", display: "block", marginBottom: 4 }}>Agent</label>
              <select style={inputStyle} value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}>
                {agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: 8 }}>
              <label style={{ fontSize: 11.5, color: "var(--txt1)", display: "block", marginBottom: 4 }}>Query</label>
              <input style={inputStyle} value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
              <div>
                <label style={{ fontSize: 11.5, color: "var(--txt1)", display: "block", marginBottom: 4 }}>Top-K</label>
                <input style={inputStyle} defaultValue="5" />
              </div>
              <div>
                <label style={{ fontSize: 11.5, color: "var(--txt1)", display: "block", marginBottom: 4 }}>Min similarity</label>
                <input style={inputStyle} defaultValue="0.82" />
              </div>
            </div>
            <button style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600, marginBottom: 12 }}>
              🔍 Run Search
            </button>
            <div style={{ height: 1, background: "var(--border)", margin: "12px 0" }} />
            <div style={{ fontSize: 11, color: "var(--txt2)", marginBottom: 8 }}>
              Enable pgvector by setting PGVECTOR_ENABLED=true and OPENAI_API_KEY in .env
            </div>
            <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--teal)", lineHeight: 1.9, background: "var(--bg2)", padding: "8px 10px", borderRadius: 6 }}>
              store_memory(session, agent_id, content)<br />
              retrieve_memory(session, agent_id, query, limit=5)<br />
              Uses pgvector cosine similarity (&lt;=&gt; operator)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}