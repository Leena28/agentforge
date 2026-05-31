import { useState } from "react";

type Channel = {
  id: string;
  name: string;
  icon: string;
  description: string;
  connected: boolean;
  module: string;
  color: string;
  bg: string;
};

const CHANNELS: Channel[] = [
  {
    id: "slack",
    name: "Slack",
    icon: "💬",
    description: "Bolt for Python · Socket Mode — no public webhook required. Handles @mentions and DMs. Sets run.channel = 'slack' and delivers final_response back to the thread.",
    connected: false,
    module: "app/channels/slack.py",
    color: "var(--blue)",
    bg: "rgba(77,142,247,.12)",
  },
  {
    id: "whatsapp",
    name: "WhatsApp Business API",
    icon: "📱",
    description: "Create app/channels/whatsapp.py · follow the same pattern as slack.py: normalize inbound webhook → create_run → execute_workflow_task.delay. Handle final_response delivery via WhatsApp send API.",
    connected: false,
    module: "app/channels/whatsapp.py",
    color: "var(--green)",
    bg: "rgba(78,203,130,.12)",
  },
  {
    id: "telegram",
    name: "Telegram Bot",
    icon: "✈️",
    description: "Create app/channels/telegram.py using python-telegram-bot. Register webhook, normalize message → create_run → execute_workflow_task.delay. Deliver final_response via bot.send_message.",
    connected: false,
    module: "app/channels/telegram.py",
    color: "var(--blue)",
    bg: "rgba(77,142,247,.12)",
  },
];

export default function ChannelsPage() {
  const [channels, setChannels] = useState(CHANNELS);
  const [slackToken, setSlackToken] = useState("");
  const [slackAppToken, setSlackAppToken] = useState("");

  const toggleConnect = (id: string) => {
    setChannels((prev) =>
      prev.map((c) => (c.id === id ? { ...c, connected: !c.connected } : c))
    );
  };

  const inputStyle = {
    padding: "7px 10px",
    border: "1px solid var(--border2)", borderRadius: 6,
    fontSize: 12, background: "var(--bg2)", color: "var(--txt0)",
    fontFamily: "inherit", outline: "none",
  };

  const connectedChannels = channels.filter((c) => c.connected);
  const availableChannels = channels.filter((c) => !c.connected);

  return (
    <div style={{ padding: 20 }}>
      <div style={{ marginBottom: 18 }}>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: "var(--txt0)" }}>Channel Management</h2>
        <p style={{ fontSize: 11.5, color: "var(--txt1)", marginTop: 2 }}>
          Connect external messaging channels — each follows the same pattern: create_run → execute_workflow_task.delay(run.id)
        </p>
      </div>

      {connectedChannels.length > 0 && (
        <>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
            Connected channels
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 18 }}>
            {connectedChannels.map((ch) => (
              <div key={ch.id} style={{ background: "var(--bg2)", border: "1px solid var(--teal)", borderRadius: 8, padding: 14, display: "flex", alignItems: "flex-start", gap: 12 }}>
                <div style={{ width: 38, height: 38, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, background: ch.bg, flexShrink: 0 }}>
                  {ch.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--txt0)", marginBottom: 2, display: "flex", alignItems: "center", gap: 6 }}>
                    {ch.name}
                    <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(0,212,170,.10)", color: "var(--teal)" }}>Connected</span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--txt2)", marginBottom: 8, lineHeight: 1.5 }}>{ch.description}</div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "var(--bg3)", color: "var(--txt1)" }}>module: {ch.module}</span>
                    <span style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 20, background: "rgba(78,203,130,.12)", color: "var(--green)" }}>Bolt running</span>
                  </div>
                </div>
                <button
                  onClick={() => toggleConnect(ch.id)}
                  style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--red)", background: "rgba(240,96,96,.12)", color: "var(--red)", cursor: "pointer", flexShrink: 0 }}
                >
                  Disconnect
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 10 }}>
        Available channels
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 18 }}>
        {availableChannels.map((ch) => (
          <div key={ch.id} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: 14, display: "flex", alignItems: "flex-start", gap: 12 }}>
            <div style={{ width: 38, height: 38, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, background: ch.bg, flexShrink: 0 }}>
              {ch.icon}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--txt0)", marginBottom: 2 }}>{ch.name}</div>
              <div style={{ fontSize: 11, color: "var(--txt2)", marginBottom: 8, lineHeight: 1.5 }}>{ch.description}</div>
              {ch.id === "slack" && (
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <input
                    style={{ ...inputStyle, width: 220 }}
                    placeholder="SLACK_BOT_TOKEN"
                    value={slackToken}
                    onChange={(e) => setSlackToken(e.target.value)}
                  />
                  <input
                    style={{ ...inputStyle, width: 220 }}
                    placeholder="SLACK_APP_TOKEN"
                    value={slackAppToken}
                    onChange={(e) => setSlackAppToken(e.target.value)}
                  />
                  <button
                    onClick={() => toggleConnect(ch.id)}
                    style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600 }}
                  >
                    🔌 Connect
                  </button>
                </div>
              )}
              {ch.id !== "slack" && (
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <input style={{ ...inputStyle, width: 280 }} placeholder={`${ch.name} API token`} />
                  <button
                    onClick={() => toggleConnect(ch.id)}
                    style={{ fontSize: 11, padding: "3px 9px", borderRadius: 6, border: "1px solid var(--teal)", background: "var(--teal)", color: "#000", cursor: "pointer", fontWeight: 600 }}
                  >
                    🔌 Connect
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>How to add a new channel</div>
        <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--teal)", lineHeight: 1.9 }}>
          1. Create backend/app/channels/your_channel.py<br />
          2. Normalize inbound to: template_key, input_message, channel, source_metadata<br />
          3. Call create_run(...) then execute_workflow_task.delay(run.id)<br />
          4. Add delivery hook for final_response if channel supports replies<br />
          5. Slack is the reference implementation — copy its pattern
        </div>
      </div>
    </div>
  );
}