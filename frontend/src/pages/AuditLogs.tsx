import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { 
  ShieldCheck, 
  Clock, 
  Database,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Card, Badge } from "../components/UI";
import { auditLogsApi, AuditLogEntry } from "../services/api";
import { cn } from "../lib/utils";

function decisionVariant(decision: string): "success" | "warning" | "default" {
  if (decision === "approved") return "success";
  if (decision === "rejected") return "warning";
  return "default";
}

export function AuditLogs() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    auditLogsApi.list({ limit: 50 })
      .then(setLogs)
      .catch((err) => setError(err?.message ?? "Failed to load audit logs"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-soft">Audit Logs</h1>
          <p className="text-slate-muted">ML underwriting decisions and loan activity records.</p>
        </div>
        <div className="flex items-center gap-2 rounded-full bg-indigo-primary/10 px-4 py-2 text-xs font-medium text-indigo-primary border border-indigo-primary/20">
          <div className="h-2 w-2 animate-pulse rounded-full bg-indigo-primary" />
          Live
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20 text-slate-muted">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          Loading audit logs…
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && logs.length === 0 && (
        <Card className="py-16 text-center text-slate-muted">
          <Database className="mx-auto mb-3 h-8 w-8 opacity-40" />
          <p>No audit logs yet. Submit a loan application to generate entries.</p>
        </Card>
      )}

      {!loading && logs.length > 0 && (
        <div className="relative space-y-6 pl-12">
          <div className="absolute left-[2.25rem] top-0 h-full w-0.5 bg-gradient-to-b from-indigo-primary via-cyan-accent to-app-bg" />

          {logs.map((log, i) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="relative"
            >
              <div className="absolute -left-[3rem] top-0 flex h-10 w-10 items-center justify-center rounded-xl bg-app-bg border border-indigo-primary/30 text-indigo-primary shadow-lg shadow-indigo-primary/10 z-10">
                <Database className="h-5 w-5" />
              </div>

              <Card className="hover:border-indigo-primary/30 transition-all">
                <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant={decisionVariant(log.decision)}>
                      {log.decision.toUpperCase()}
                    </Badge>
                    <span className="text-sm font-semibold text-slate-soft">
                      Model v{log.model_version}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-muted">
                    <Clock className="h-3 w-3" />
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="mb-1 text-xs font-medium uppercase tracking-wider text-slate-muted">Risk Score</p>
                    <p className={cn(
                      "text-lg font-bold",
                      log.prediction_score >= 0.7 ? "text-red-400" : log.prediction_score >= 0.4 ? "text-yellow-400" : "text-green-400"
                    )}>
                      {(log.prediction_score * 100).toFixed(1)}%
                    </p>
                  </div>
                  {log.confidence !== undefined && (
                    <div>
                      <p className="mb-1 text-xs font-medium uppercase tracking-wider text-slate-muted">Confidence</p>
                      <p className="text-lg font-bold text-slate-soft">{(log.confidence * 100).toFixed(1)}%</p>
                    </div>
                  )}
                </div>

                <div className="mt-3 flex items-center gap-2 text-xs text-indigo-primary/60 border-t border-white/5 pt-3">
                  <ShieldCheck className="h-3 w-3" />
                  Loan ID: {log.loan_id?.slice(0, 8) ?? 'N/A'}…
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
