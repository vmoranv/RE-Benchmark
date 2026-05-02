import { useTranslation } from "react-i18next";

const NAV_ITEMS = [
  "leaderboard",
  "runs",
  "samples",
  "submit",
  "dashboard",
  "reports",
] as const;

export function Sidebar() {
  const { t } = useTranslation();
  return (
    <aside className="flex flex-col border-r border-zinc-200 bg-white px-4 py-6 dark:border-zinc-800 dark:bg-zinc-950" role="navigation" aria-label="Main navigation">
      <div className="mb-8">
        <div className="font-mono text-base font-semibold">{t("app.name")}</div>
        <div className="text-xs text-zinc-500">{t("app.tagline")}</div>
      </div>
      <nav className="flex flex-col gap-1 text-sm">
        {NAV_ITEMS.map((key) => (
          <button
            key={key}
            type="button"
            className="rounded-md px-3 py-2 text-left text-zinc-700 transition hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            {t(`nav.${key}`)}
          </button>
        ))}
      </nav>
    </aside>
  );
}
