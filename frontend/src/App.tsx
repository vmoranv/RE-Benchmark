import { useTranslation } from "react-i18next";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { Leaderboard } from "@/routes/Leaderboard";

export function App() {
  const { t } = useTranslation();
  return (
    <div className="grid min-h-screen grid-cols-[16rem_1fr]">
      <Sidebar />
      <div className="flex flex-col">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6" role="main">
          <h1 className="mb-6 text-2xl font-semibold tracking-tight">
            {t("nav.leaderboard")}
          </h1>
          <Leaderboard />
        </main>
      </div>
    </div>
  );
}
