import { useEffect, useState } from "react";
import { getTemplates, startRun } from "../../services/api";
import { useAppStore } from "../../store";
import type { WorkflowTemplate, WorkflowNode, WorkflowEdge } from "../../types";

const nodeColor = (type: string) => {
  switch (type) {
    case "agent": return { border: "var(--teal)", dot: "var(--teal)" };
    case "tool": return { border: "var(--amber)", dot: "var(--amber)" };
    case "approval": return { border: "var(--red)", dot: "var(--red)" };
    case "channel": return { border: "var(--blue)", dot: "var(--blue)" };
    default: return { border: "var(--border2)", dot: "var(--txt2)" };
  }
};

export default function WorkflowBuilderPage() {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [selected, setSelected] = useState<WorkflowTemplate | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [inputMessage, setInputMessage] = useState("");
  const [running, setRunning] = useState(false);
  const { setActivePage, setActiveRunId } = useAppStore();

  useEffect(() => {
    getTemplates().then((data) => {
      setTemplates(data);
      if (data.length > 0) {
        setSelected(data[0]);
        setInputMessage(data[0].default_input);
      }
    });
  }, []);

  const handleRun = async () => {
    if (!selected || !inputMessage) return;
    setRunning(true);
    try {
      const result = await startRun({
        template_key: selected.key,
        input_message: inputMessage,
        channel: "web",
      });
      setActiveRunId(result.run_id);
      setActivePage("monitor");
    } catch {
      alert("Failed to start run.");
    } finally {
      setRunning(false);
    }
  };

  const canvasWidth = 700;
  const canvasHeight = 200;

  const scaleNode = (node: WorkflowNode) => ({
    ...node,
    x: Math.min((node.x / 1400) * canvasWidth, canvasWidth - 130),
    y: Math.min((node.y / 400) * canvasHeight, canvasHeight - 60),
  });

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>Workflow Builder</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>
            {selected?.name || "Select a template"} · React Flow canvas · configure and run
          </p>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={() => setActivePage("templates")} style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--border2)", background: "var(--bg2)", color: "var(--txt0)", cursor: "pointer" }}>
            📋 Templates
          </button>
          <button onClick={() => setActivePage("templates")} style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--border2)", background: "var(--bg2)", color: "var(--txt0)", cursor: "pointer" }}>
            💾 Save as Template
          </button>
          <button
            onClick={handleRun}
            disabled={running}
            style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600, opacity: running ? 0.7 : 1 }}
          >
            {running ? "Starting..." : "▶ Run"}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        {templates.map((t) => (
          <button
            key={t.key}
            onClick={() => { setSelected(t); setInputMessage(t.default_input); setSelectedNode(null); }}
            style={{
              fontSize: 11, padding: "4px 12px", borderRadius: 20,
              border: `1px solid ${selected?.key === t.key ? "var(--teal)" : "var(--border2)"}`,
              background: selected?.key === t.key ? "rgba(0,212,170,.10)" : "var(--bg2)",
              color: selected?.key === t.key ? "var(--teal)" : "var(--txt1)",
              cursor: "pointer",
            }}
          >
            {t.name}
          </button>
        ))}
      </div>

      {selected && (
        <>
          <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, position: "relative", height: 220, overflow: "hidden", marginBottom: 12 }}>
            <div style={{ fontSize: 10.5, color: "var(--txt2)", padding: "7px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 5 }}>
              🖱️ Click a node to configure · Run to execute workflow
            </div>
            <div style={{ position: "relative", height: 180, margin: "0 10px" }}>
              {selected.graph.edges?.map((edge: WorkflowEdge, i: number) => {
                const fromNode = selected.graph.nodes?.find((n) => n.id === edge.source);
                const toNode = selected.graph.nodes?.find((n) => n.id === edge.target);
                if (!fromNode || !toNode) return null;
                const from = scaleNode(fromNode);
                const to = scaleNode(toNode);
                const x1 = from.x + 120;
                const y1 = from.y + 28;
                const x2 = to.x;
                const y2 = to.y + 28;
                return (
                  <svg key={i} style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
                    <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--border2)" strokeWidth={1.5} markerEnd="url(#arrow)" />
                    <defs>
                      <marker id="arrow" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
                        <path d="M0,0 L0,6 L6,3 z" fill="var(--border2)" />
                      </marker>
                    </defs>
                  </svg>
                );
              })}
              {selected.graph.nodes?.map((node: WorkflowNode) => {
                const scaled = scaleNode(node);
                const colors = nodeColor(node.type);
                const isSelected = selectedNode?.id === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    style={{
                      position: "absolute",
                      left: scaled.x, top: scaled.y,
                      background: "var(--bg1)",
                      border: `1px solid ${isSelected ? colors.border : "var(--border2)"}`,
                      boxShadow: isSelected ? `0 0 0 1px ${colors.border}` : "none",
                      borderRadius: 8, padding: "8px 11px",
                      fontSize: 11.5, width: 120, cursor: "pointer",
                    }}
                  >
                    <div style={{ fontWeight: 600, color: "var(--txt0)", marginBottom: 1 }}>{node.label}</div>
                    <div style={{ color: "var(--txt2)", fontSize: 10 }}>{node.type} · {node.id}</div>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: colors.dot, position: "absolute", right: -4, top: "50%", transform: "translateY(-50%)", border: "1px solid var(--bg0)" }} />
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>
                {selectedNode ? `Selected node — ${selectedNode.label}` : "Select a node to configure"}
              </div>
              {selectedNode ? (
                <>
                  <div style={{ marginBottom: 8 }}>
                    <label style={{ fontSize: 11.5, color: "var(--txt1)", display: "block", marginBottom: 4 }}>Node type</label>
                    <input style={{ width: "100%", padding: "7px 10px", border: "1px solid var(--border2)", borderRadius: 6, fontSize: 12, background: "var(--bg2)", color: "var(--txt0)", fontFamily: "inherit", outline: "none" }} value={selectedNode.type} readOnly />
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <label style={{ fontSize: 11.5, color: "var(--txt1)", display: "block", marginBottom: 4 }}>Node ID</label>
                    <input style={{ width: "100%", padding: "7px 10px", border: "1px solid var(--border2)", borderRadius: 6, fontSize: 12, background: "var(--bg2)", color: "var(--txt0)", fontFamily: "inherit", outline: "none" }} value={selectedNode.id} readOnly />
                  </div>
                  <div style={{ fontSize: 11, color: "var(--txt2)", padding: "8px", background: "var(--bg2)", borderRadius: 6 }}>
                    Agent config is loaded from DB at runtime via runtime_node_binding. Edit the agent to change system_prompt, model, and guardrails.
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 11, color: "var(--txt2)" }}>Click any node in the canvas above to see its configuration.</div>
              )}
            </div>

            <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 10 }}>Run this workflow</div>
              <div style={{ marginBottom: 8 }}>
                <label style={{ fontSize: 11.5, color: "var(--txt1)", display: "block", marginBottom: 4 }}>Input message</label>
                <textarea
                  style={{ width: "100%", padding: "7px 10px", border: "1px solid var(--border2)", borderRadius: 6, fontSize: 12, background: "var(--bg2)", color: "var(--txt0)", fontFamily: "monospace", outline: "none", resize: "none", height: 80 }}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                />
              </div>
              <button
                onClick={handleRun}
                disabled={running}
                style={{ fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600, opacity: running ? 0.7 : 1 }}
              >
                {running ? "Starting..." : "▶ Run Workflow"}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}