import { useAppStore } from "./store";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import AgentsPage from "./pages/Agents";
import NewAgentPage from "./pages/NewAgent";
import WorkflowBuilderPage from "./pages/WorkflowBuilder";
import TemplatesPage from "./pages/Templates";
import LiveMonitorPage from "./pages/LiveMonitor";
import RunHistoryPage from "./pages/RunHistory";
import SchedulerPage from "./pages/Scheduler";
import MemoryPage from "./pages/Memory";
import ChannelsPage from "./pages/Channels";

export default function App() {
  const { activePage } = useAppStore();

  const renderPage = () => {
    switch (activePage) {
      case "agents": return <AgentsPage />;
      case "create": return <NewAgentPage />;
      case "workflow": return <WorkflowBuilderPage />;
      case "templates": return <TemplatesPage />;
      case "monitor": return <LiveMonitorPage />;
      case "runs": return <RunHistoryPage />;
      case "scheduler": return <SchedulerPage />;
      case "memory": return <MemoryPage />;
      case "channels": return <ChannelsPage />;
      default: return <AgentsPage />;
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "var(--bg0)", color: "var(--txt0)" }}>
      <Topbar />
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <Sidebar />
        <main style={{ flex: 1, overflowY: "auto", background: "var(--bg0)" }}>
          {renderPage()}
        </main>
      </div>
    </div>
  );
}