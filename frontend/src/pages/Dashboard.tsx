import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  BarChart, Bar, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { useMetricsSummary } from "../hooks/useApi";
import { format, parseISO } from "date-fns";

const SEV_COLOR: Record<string, string> = {
  low: "#facc15",
  medium: "#fb923c",
  high: "#f87171",
};

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">{label}</p>
      <p className="text-3xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading } = useMetricsSummary();

  if (isLoading) return <div className="p-8 text-gray-500">Loading metrics...</div>;
  if (!data) return null;

  const totalAnomalies = Object.values(data.anomalies_by_severity).reduce((a, b) => a + b, 0);
  const anomalyRate = data.total_logs_ingested
    ? ((totalAnomalies / data.total_logs_ingested) * 100).toFixed(2)
    : "0.00";

  const timeData = data.anomalies_over_time.map((d) => ({
    time: format(parseISO(d.timestamp), "HH:mm"),
    count: d.count,
  }));

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">System Overview</h1>
        <p className="text-gray-500 text-sm mt-1">Real-time anomaly detection · refreshes every 10s</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Logs Ingested" value={data.total_logs_ingested.toLocaleString()} sub="from Kafka" />
        <StatCard label="Total Anomalies" value={totalAnomalies} />
        <StatCard label="Anomaly Rate" value={`${anomalyRate}%`} />
        <StatCard
          label="High Severity"
          value={data.anomalies_by_severity["high"] ?? 0}
          sub="requires immediate action"
        />
      </div>

      {/* Anomaly severity breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {["low", "medium", "high"].map((sev) => (
          <div key={sev} className="bg-gray-900 border border-gray-800 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full" style={{ background: SEV_COLOR[sev] }} />
              <span className="text-xs uppercase tracking-widest text-gray-400">{sev} severity</span>
            </div>
            <p className="text-4xl font-bold" style={{ color: SEV_COLOR[sev] }}>
              {data.anomalies_by_severity[sev] ?? 0}
            </p>
          </div>
        ))}
      </div>

      {/* Timeline chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm text-gray-400 uppercase tracking-widest mb-4">Anomalies Over Time</h2>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={timeData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 11 }} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151", color: "#f9fafb" }} />
            <Area type="monotone" dataKey="count" stroke="#4ade80" fill="#4ade8010" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Top services */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm text-gray-400 uppercase tracking-widest mb-4">Top Offending Services</h2>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={data.top_services} layout="vertical">
            <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }} />
            <YAxis type="category" dataKey="service" tick={{ fill: "#d1d5db", fontSize: 12 }} width={140} />
            <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151", color: "#f9fafb" }} />
            <Bar dataKey="count" fill="#4ade80" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
