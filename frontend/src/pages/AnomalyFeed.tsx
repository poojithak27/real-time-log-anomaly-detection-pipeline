import { useState } from "react";
import { useAnomalies, type Anomaly } from "../hooks/useApi";
import { formatDistanceToNow, parseISO } from "date-fns";

const SEV_BADGE: Record<string, string> = {
  low:    "bg-yellow-400/10 text-yellow-400 border border-yellow-400/20",
  medium: "bg-orange-400/10 text-orange-400 border border-orange-400/20",
  high:   "bg-red-400/10 text-red-400 border border-red-400/20",
};

function AnomalyRow({ a }: { a: Anomaly }) {
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
      <td className="px-4 py-3 text-xs text-gray-500">
        {formatDistanceToNow(parseISO(a.timestamp), { addSuffix: true })}
      </td>
      <td className="px-4 py-3">
        <span className={`text-xs px-2 py-0.5 rounded font-mono uppercase ${SEV_BADGE[a.severity]}`}>
          {a.severity}
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-blue-400 font-mono">{a.service}</td>
      <td className="px-4 py-3 text-sm text-gray-300 max-w-md truncate">{a.message}</td>
      <td className="px-4 py-3 text-xs text-gray-500 font-mono">
        {a.anomaly_score.toFixed(3)}
      </td>
    </tr>
  );
}

export default function AnomalyFeed() {
  const [severity, setSeverity] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useAnomalies({
    ...(severity && { severity }),
    ...(q && { q }),
    page,
    page_size: 25,
  });

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Anomaly Feed</h1>
        <p className="text-gray-500 text-sm mt-1">All detected anomalies · auto-refreshes every 10s</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Search log messages..."
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 w-72 focus:outline-none focus:border-green-500"
        />
        <select
          value={severity}
          onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-green-500"
        >
          <option value="">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-gray-500 text-center">Loading...</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-widest">
                <th className="px-4 py-3 text-left">Time</th>
                <th className="px-4 py-3 text-left">Severity</th>
                <th className="px-4 py-3 text-left">Service</th>
                <th className="px-4 py-3 text-left">Message</th>
                <th className="px-4 py-3 text-left">Score</th>
              </tr>
            </thead>
            <tbody>
              {data?.results.map((a) => <AnomalyRow key={a.id} a={a} />)}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <button
          disabled={page === 1}
          onClick={() => setPage((p) => p - 1)}
          className="px-3 py-1 border border-gray-700 rounded disabled:opacity-30 hover:border-green-500 transition-colors"
        >
          ← Prev
        </button>
        <span>Page {page} · {data?.total ?? 0} total</span>
        <button
          disabled={!data || page * 25 >= data.total}
          onClick={() => setPage((p) => p + 1)}
          className="px-3 py-1 border border-gray-700 rounded disabled:opacity-30 hover:border-green-500 transition-colors"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
