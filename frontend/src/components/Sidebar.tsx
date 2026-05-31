import { useAppStore } from "../store";

type NavItem = {
  id: string;
  label: string;
  icon: string;
  badge?: string;
  badgeRed?: boolean;
};

const navItems: NavItem[] = [
  { id: "agents", label: "Agents", icon: "🤖", badge: "5" },
  { id: "workflow", label: "Workflow Builder", icon: "🔀" },
  { id: "templates", label: "Templates", icon: "📋" },
  { id: "monitor", label: "Live Monitor", icon: "📡", badge: "●" },
  { id: "runs", label: "Run History", icon: "📜" },
];

const configItems: NavItem[] = [
  { id: "create", label: "New Agent", icon: "➕" },
  { id: "scheduler", label: "Scheduler", icon: "⏰" },
  { id: "memory", label: "Memory / pgvector", icon: "🧠" },
  { id: "channels", label: "Channels", icon: "🔌", badge: "!", badgeRed: true },
];

export default function Sidebar() {
  const { activePage, setActivePage } = useAppStore();

  const NavLink = ({ item }: { item: NavItem }) => (
    <div
      onClick={() => setActivePage(item.id)}
      style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "8px 14px", fontSize: 12.5,
        color: activePage === item.id ? "var(--teal)" : "var(--txt1)",
        cursor: "pointer",
        borderLeft: activePage === item.id ? "2px solid var(--teal)" : "2px solid transparent",
        background: activePage === item.id ? "var(--bg2)" : "transparent",
        transition: "all 0.12s",
      }}
      onMouseEnter={(e) => {
        if (activePage !== item.id) {
          (e.currentTarget as HTMLDivElement).style.background = "var(--bg2)";
          (e.currentTarget as HTMLDivElement).style.color = "var(--txt0)";
        }
      }}
      onMouseLeave={(e) => {
        if (activePage !== item.id) {
          (e.currentTarget as HTMLDivElement).style.background = "transparent";
          (e.currentTarget as HTMLDivElement).style.color = "var(--txt1)";
        }
      }}
    >
      <span style={{ fontSize: 15, flexShrink: 0 }}>{item.icon}</span>
      <span style={{ flex: 1 }}>{item.label}</span>
      {item.badge && (
        <span style={{
          fontSize: 10, padding: "1px 6px", borderRadius: 10,
          background: item.badgeRed ? "rgba(240,96,96,.12)" : "rgba(0,212,170,.10)",
          color: item.badgeRed ? "var(--red)" : "var(--teal)",
          fontWeight: 600,
        }}>
          {item.badge}
        </span>
      )}
    </div>
  );

  return (
    <div style={{
      width: 192, background: "var(--bg1)",
      borderRight: "1px solid var(--border)",
      display: "flex", flexDirection: "column",
      flexShrink: 0, overflowY: "auto",
    }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".08em", padding: "14px 14px 5px" }}>
        Platform
      </div>
      {navItems.map((item) => <NavLink key={item.id} item={item} />)}

      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--txt2)", textTransform: "uppercase", letterSpacing: ".08em", padding: "14px 14px 5px" }}>
        Config
      </div>
      {configItems.map((item) => <NavLink key={item.id} item={item} />)}

      <div style={{ marginTop: "auto", padding: "10px 0", borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 14px", fontSize: 12.5, color: "var(--txt1)", cursor: "pointer" }}>
          <span>⚙️</span> Settings
        </div>
      </div>
    </div>
  );
}