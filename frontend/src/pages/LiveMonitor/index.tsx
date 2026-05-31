import { useEffect, useState, useRef } from "react";
import { getRun, approveRun, createEventStream } from "../../services/api";
import { useAppStore } from "../../store";
import type { WorkflowRun, RunEvent, AgentMessage } from "../../types";

const eventColor = (type: string) => {
  if (type.includes("started")) return "var(--blue)";
  if (type.includes("agent") || type.includes("decision")) return "var(--blue)";
  if (type.includes("tool")) return "var(--amber)";
  if (type.includes("llm")) return "var(--purple)";
  if (type.includes("approval") || type.includes("gate")) return "var(--amber)";
  if (type.includes("completed")) return "var(--green)";
  if (type.includes("failed")) return "var(--red)";
  return "var(--txt1)";
};

const statusBadge = (status: string) => {
  switch (status) {
    case "completed": return { bg: "rgba(78,203,130,.12)", color: "var(--green)", label: "Completed" };
    case "running": return { bg: "rgba(0,212,170,.10)", color: "var(--teal)", label: "Running" };
    case "awaiting_approval": return { bg: "rgba(245,166,35,.12)", color: "var(--amber)", label: "Awaiting Approval" };
    case "failed": return { bg: "rgba(240,96,96,.12)", color: "var(--red)", label: "Failed" };
    default: return { bg: "var(--bg3)", color: "var(--txt1)", label: status };
  }
};

export default function LiveMonitorPage() {
  const { activeRunId, setActivePage } = useAppStore();
  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [approving, setApproving] = useState(false);
  const eventsEndRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!activeRunId) return;

    getRun(activeRunId).then(setRun);

    const es = createEventStream(activeRunId);
    esRef.current = es;
    setConnected(true);

    es.addEventListener("run_event", (e: MessageEvent) => {
      const data = JSON.parse(e.data) as RunEvent;
      setEvents((prev) => [...prev, data]);
    });

    es.addEventListener("run_status", (e: MessageEvent) => {
      const { status } = JSON.parse(e.data);
      setRun((prev) => prev ? { ...prev, status } : null);
      setConnected(false);
      es.close();
      getRun(activeRunId).then(setRun);
    });

    es.onerror = () => {
      setConnected(false);
      es.close();
    };

    return () => {
      es.close();
    };
  }, [activeRunId]);

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const handleApprove = async () => {
    if (!activeRunId) return;
    setApproving(true);
    try {
      const updated = await approveRun(activeRunId, { approved_by: "operator" });
      setRun(updated);
    } catch {
      alert("Failed to approve run.");
    } finally {
      setApproving(false);
    }
  };

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString("en-US", { hour12: false });

  if (!activeRunId) {
    return (
      <div style={{ padding: 20 }}>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)", marginBottom: 12 }}>Live Monitor</h2>
        <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: 24, textAlign: "center", color: "var(--txt2)" }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📡</div>
          <div style={{ fontSize: 13, marginBottom: 12 }}>No active run. Start a workflow to see live events.</div>
          <button
            onClick={() => setActivePage("workflow")}
            style={{ fontSize: 12, padding: "5px 12px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600 }}
          >
            ▶ Start a Workflow
          </button>
        </div>
      </div>
    );
  }

  const badge = run ? statusBadge(run.status) : null;

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>Live Monitor</h2>
          <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>SSE event stream — real-time events push from the backend as they happen</p>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: connected ? "rgba(0,212,170,.10)" : "var(--bg3)", color: connected ? "var(--teal)" : "var(--txt2)", display: "inline-flex", alignItems: "center", gap: 4 }}>
            {connected && <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--teal)", display: "inline-block" }} />}
            {connected ? `SSE connected · ${activeRunId.slice(0, 8)}` : "SSE disconnected"}
          </span>
          {badge && (
            <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: badge.bg, color: badge.color, fontWeight: 500 }}>
              {badge.label}
            </span>
          )}
          {run?.status === "awaiting_approval" && (
            <button
              onClick={handleApprove}
              disabled={approving}
              style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600, opacity: approving ? 0.7 : 1 }}
            >
              {approving ? "Approving..." : "✓ Approve Run"}
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 18 }}>
        {[
          { label: "Token count", value: run?.token_count ?? 0 },
          { label: "Est. cost USD", value: `$${(run?.estimated_cost_usd ?? 0).toFixed(4)}` },
          { label: "Confidence", value: run?.confidence ? `${(run.confidence * 100).toFixed(0)}%` : "—" },
          { label: "Events", value: events.length },
        ].map((m) => (
          <div key={m.label} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px 14px" }}>
            <div style={{ fontSize: 10.5, color: "var(--txt2)", marginBottom: 4 }}>{m.label}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--txt0)", fontFamily: "monospace" }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
            Live SSE event stream
            <span style={{ fontFamily: "monospace", fontSize: 10, color: "var(--txt2)", marginLeft: 6 }}>
              /api/runs/{activeRunId?.slice(0, 8)}.../events/stream
            </span>
          </div>
          <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: "10px 14px", maxHeight: 320, overflowY: "auto" }}>
            {events.length === 0 && (
              <div style={{ fontSize: 11, color: "var(--txt2)", textAlign: "center", padding: 20 }}>
                {connected ? "Waiting for events..." : "No events yet."}
              </div>
            )}
            {events.map((ev) => (
              <div key={ev.id} style={{ display: "flex", gap: 10, padding: "7px 0", borderBottom: "1px solid var(--border)", animation: "fadein .2s" }}>
                <span style={{ fontFamily: "monospace", fontSize: 10.5, color: "var(--txt2)", flexShrink: 0, width: 70 }}>
                  {formatTime(ev.created_at)}
                </span>
                <span style={{ fontSize: 11.5, flex: 1 }}>
                  <strong style={{ color: eventColor(ev.event_type) }}>{ev.event_type}</strong>
                  {" · "}{ev.title}
                  {ev.token_count > 0 && (
                    <span style={{ display: "block", fontSize: 10.5, fontFamily: "monospace", color: "var(--txt2)" }}>
                      {ev.token_count} tokens · ${ev.cost_usd.toFixed(4)}
                    </span>
                  )}
                </span>
                {ev.node_id && (
                  <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "var(--bg3)", color: "var(--txt1)", flexShrink: 0 }}>
                    {ev.node_id}
                  </span>
                )}
              </div>
            ))}
            <div ref={eventsEndRef} />
          </div>
        </div>

        <div>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
            Inter-agent messages
          </div>
          <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: "10px 14px", marginBottom: 12, maxHeight: 200, overflowY: "auto" }}>
            {(run?.messages || []).length === 0 && (
              <div style={{ fontSize: 11, color: "var(--txt2)", textAlign: "center", padding: 12 }}>No messages yet.</div>
            )}
            {(run?.messages || []).map((msg: AgentMessage) => (
              <div key={msg.id} style={{ display: "flex", gap: 10, padding: "8px 0", borderBottom: "1px solid var(--border)", fontSize: 11.5, alignItems: "flex-start", paddingLeft: 10, borderLeft: "2px solid var(--teal)", marginBottom: 4 }}>
                <span style={{ color: "var(--txt2)", flexShrink: 0, width: 68, fontFamily: "monospace", fontSize: 10.5 }}>
                  {formatTime(msg.created_at)}
                </span>
                <span style={{ fontWeight: 600, flexShrink: 0, width: 108, color: "var(--teal)" }}>{msg.sender}</span>
                <span style={{ color: "var(--txt1)", flex: 1, lineHeight: 1.45 }}>
                  → {msg.recipient}: {msg.content.slice(0, 80)}...
                </span>
              </div>
            ))}
          </div>

          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
            Final response
          </div>
          <div style={{ background: "var(--bg1)", border: "1px solid var(--border)", borderRadius: 12, padding: "10px 14px" }}>
            {run?.final_response ? (
              <div style={{ fontSize: 12, color: "var(--txt0)", lineHeight: 1.6 }}>{run.final_response}</div>
            ) : (
              <div style={{ fontSize: 11, color: "var(--txt2)" }}>Waiting for workflow to complete...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}