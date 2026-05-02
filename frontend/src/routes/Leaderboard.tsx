import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

interface DimensionItem {
  code: string;
  implemented: boolean;
  milestone: string;
}

async function fetchDimensions(): Promise<DimensionItem[]> {
  const res = await fetch("/api/v1/dimensions/");
  if (!res.ok) throw new Error("failed to load dimensions");
  const body = (await res.json()) as { items: DimensionItem[] };
  return body.items;
}

export function Leaderboard() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["dimensions"],
    queryFn: fetchDimensions,
  });

  if (isLoading) return <div className="text-zinc-500">{t("common.loading")}</div>;
  if (!data || data.length === 0)
    return <div className="text-zinc-500">{t("leaderboard.empty")}</div>;

  return (
    <div className="bench-card overflow-hidden">
      <table className="w-full text-left text-sm" role="table">
        <thead className="bg-zinc-50 text-xs uppercase text-zinc-500 dark:bg-zinc-900">
          <tr>
            <th className="px-4 py-2" scope="col">Dimension</th>
            <th className="px-4 py-2" scope="col">Status</th>
            <th className="px-4 py-2" scope="col">Milestone</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d) => (
            <tr
              key={d.code}
              className="border-t border-zinc-100 dark:border-zinc-900"
            >
              <td className="px-4 py-2 font-mono" scope="row">{d.code}</td>
              <td className="px-4 py-2">
                <span
                  className={
                    d.implemented ? "bench-tag-pass" : "bench-tag-warn"
                  }
                >
                  {d.implemented ? "implemented" : "placeholder"}
                </span>
              </td>
              <td className="px-4 py-2 text-zinc-500">{d.milestone}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
