import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAlertRules, alertRulesApi, type AlertRule } from "../hooks/useApi";

function RuleRow({ rule, onDelete }: { rule: AlertRule; onDelete: () => void }) {
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
      <td className="px-4 py-3 text-white font-medium">{rule.name}</td>
      <td className="px-4 py-3 text-xs text-blue-400 font-mono truncate max-w-xs">{rule.webhook_url}</td>
      <td className="px-4 py-3">
        <span className={`text-xs px-2 py-0.5 rounded uppercase font-mono ${
          rule.min_severity === "high"
            ? "bg-red-400/10 text-red-400"
            : rule.min_severity === "medium"
            ? "bg-orange-400/10 text-orange-400"
            : "bg-yellow-400/10 text-yellow-400"
        }`}>
          {rule.min_severity}+
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-gray-400">{rule.service_filter ?? "all services"}</td>
      <td className="px-4 py-3">
        <span className={`text-xs ${rule.active ? "text-green-400" : "text-gray-600"}`}>
          {rule.active ? "● active" : "○ inactive"}
        </span>
      </td>
      <td className="px-4 py-3">
        <button onClick={onDelete} className="text-xs text-red-500 hover:text-red-400 transition-colors">
          Delete
        </button>
      </td>
    </tr>
  );
}

export default function AlertRules() {
  const { data: rules = [], isLoading } = useAlertRules();
  const qc = useQueryClient();

  const [form, setForm] = useState({
    name: "", webhook_url: "", min_severity: "high", service_filter: "", active: true,
  });
  const [saving, setSaving] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await alertRulesApi.create({ ...form, service_filter: form.service_filter || null });
      qc.invalidateQueries({ queryKey: ["alert-rules"] });
      setForm({ name: "", webhook_url: "", min_severity: "high", service_filter: "", active: true });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    await alertRulesApi.delete(id);
    qc.invalidateQueries({ queryKey: ["alert-rules"] });
  }

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Alert Rules</h1>
        <p className="text-gray-500 text-sm mt-1">Configure webhook dispatch rules by severity and service</p>
      </div>

      {/* Create form */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-sm text-gray-400 uppercase tracking-widest mb-4">New Rule</h2>
        <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
          <input
            required
            placeholder="Rule name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-green-500"
          />
          <input
            required
            type="url"
            placeholder="Webhook URL (https://...)"
            value={form.webhook_url}
            onChange={(e) => setForm({ ...form, webhook_url: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-green-500"
          />
          <select
            value={form.min_severity}
            onChange={(e) => setForm({ ...form, min_severity: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-green-500"
          >
            <option value="low">Low+</option>
            <option value="medium">Medium+</option>
            <option value="high">High only</option>
          </select>
          <input
            placeholder="Service filter (optional)"
            value={form.service_filter}
            onChange={(e) => setForm({ ...form, service_filter: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-green-500"
          />
          <button
            type="submit"
            disabled={saving}
            className="col-span-2 bg-green-500 hover:bg-green-400 text-black font-bold py-2 rounded text-sm transition-colors disabled:opacity-50"
          >
            {saving ? "Saving..." : "Create Rule"}
          </button>
        </form>
      </div>

      {/* Rules table */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-gray-500 text-center">Loading...</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-widest">
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Webhook</th>
                <th className="px-4 py-3 text-left">Min Severity</th>
                <th className="px-4 py-3 text-left">Service</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left"></th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <RuleRow key={r.id} rule={r} onDelete={() => handleDelete(r.id)} />
              ))}
              {rules.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-600">No rules configured</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
