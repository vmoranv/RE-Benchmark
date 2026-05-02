import { useTranslation } from "react-i18next";
import i18n from "@/i18n";

export function TopBar() {
  const { t } = useTranslation();
  const toggleLang = () => {
    const next = i18n.language.startsWith("zh") ? "en" : "zh";
    void i18n.changeLanguage(next);
  };
  return (
    <header className="flex h-14 items-center justify-between border-b border-zinc-200 bg-white px-6 dark:border-zinc-800 dark:bg-zinc-950" role="banner" aria-label="Top bar">
      <input
        type="search"
        placeholder={t("common.loading")}
        className="w-72 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-bench-accent dark:border-zinc-800 dark:bg-zinc-900"
      />
      <div className="flex items-center gap-3 text-sm">
        <button
          type="button"
          onClick={toggleLang}
          className="rounded-md border border-zinc-200 px-2 py-1 font-mono text-xs dark:border-zinc-800"
        >
          {i18n.language.startsWith("zh") ? "EN" : "中"}
        </button>
      </div>
    </header>
  );
}
