import { useEffect, useState } from "react";
import { getTemplates } from "../../services/api";
import { useAppStore } from "../../store";
import type { WorkflowTemplate } from "../../types";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const { setActivePage } = useAppStore();

  useEffect(() => {
    getTemplates().then((data) => {
      setTemplates(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const builtin = templates.filter((t) => t.is_builtin);
  const custom = templates.filter((t) => !t.is_builtin);

  if (loading) return <div style={{ padding: 20, color: "var(--txt2)" }}>Loading templates...</div>;

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>Workflow Templates</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>Built-in and custom templates — save from the builder or add in seed.py</p>
        </div>
        <button
          onClick={() => setActivePage("workflow")}
          style={{ fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600 }}
        >
          + Create from Builder
        </button>
      </div>

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
        Built-in templates
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 18 }}>
        {builtin.map((t) => (
          <div key={t.key} style={{ background: "var(--bg1)", border: "1px solid var(--border2)", borderRadius: 12, padding: 14, cursor: "pointer", transition: "border-color .12s" }}
            onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "var(--teal)"}
            onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border2)"}
            onClick={() => setActivePage("workflow")}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{t.name}</div>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(0,212,170,.18)", color: "var(--teal)", fontWeight: 500 }}>Built-in</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--txt2)", marginBottom: 10, lineHeight: 1.6 }}>{t.description}</div>
            <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "var(--bg3)", color: "var(--txt1)" }}>key: {t.key}</span>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "var(--bg3)", color: "var(--txt1)" }}>{t.graph.nodes?.length || 0} nodes</span>
            </div>
            <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--teal)", background: "var(--bg2)", padding: "6px 8px", borderRadius: 6, lineHeight: 1.6 }}>
              {t.graph.nodes?.map((n) => n.id).join(" → ")}
            </div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
        Custom templates
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 18 }}>
        {custom.map((t) => (
          <div key={t.key} style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{t.name}</div>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(167,139,250,.12)", color: "var(--purple)", fontWeight: 500 }}>Custom</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--txt2)", marginBottom: 10 }}>{t.description}</div>
            <div style={{ display: "flex", gap: 6 }}>
              <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "var(--bg3)", color: "var(--txt1)" }}>key: {t.key}</span>
              <button style={{ fontSize: 11, padding: "2px 8px", borderRadius: 6, border: "1px solid var(--red)", background: "rgba(240,96,96,.12)", color: "var(--red)", cursor: "pointer" }}>
                🗑️ Delete
              </button>
            </div>
          </div>
        ))}
        <div
          onClick={() => setActivePage("workflow")}
          style={{ background: "var(--bg1)", border: "1px dashed var(--border2)", borderRadius: 12, padding: 14, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, cursor: "pointer", color: "var(--txt2)", fontSize: 12 }}
          onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "var(--teal)"}
          onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border2)"}
        >
          + Build and save a new template
        </div>
      </div>

      <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>How to add a workflow template</div>
        <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--teal)", lineHeight: 1.9 }}>
          1. Add graph definition to backend/app/seed.py<br />
          2. Add entry to BUILTIN_TEMPLATES with key, name, description, graph, default_input<br />
          3. Add or reuse LangGraph nodes in langgraph_runtime.py<br />
          4. Restart — templates are upserted on startup via seed()
        </div>
      </div>
    </div>
  );
}