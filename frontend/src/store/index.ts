import { create } from "zustand";

type AppStore = {
  activeRunId: string | null;
  activePage: string;
  setActiveRunId: (id: string | null) => void;
  setActivePage: (page: string) => void;
};

export const useAppStore = create<AppStore>((set) => ({
  activeRunId: null,
  activePage: "agents",
  setActiveRunId: (id) => set({ activeRunId: id }),
  setActivePage: (page) => set({ activePage: page }),
}));