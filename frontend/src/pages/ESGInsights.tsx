import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { 
  Leaf, 
  Wind, 
  Recycle, 
  Users, 
  ShieldCheck,
  TrendingUp,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
} from "recharts";
import { Card, Badge, Button } from "../components/UI";
import { esgApi, ESGMetricsResponse } from "../services/api";
import { cn } from "../lib/utils";

const BENCHMARK_DATA = [
  { category: "Energy", yourScore: 85, industryAvg: 45 },
  { category: "Waste", yourScore: 65, industryAvg: 50 },
  { category: "Social", yourScore: 88, industryAvg: 72 },
  { category: "Governance", yourScore: 92, industryAvg: 80 },
];

export function ESGInsights() {
  const [metrics, setMetrics] = useState<ESGMetricsResponse | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Form state mirrors the current metric values
  const [renewableEnergy, setRenewableEnergy] = useState<string>("");
  const [carbonIntensity, setCarbonIntensity] = useState<string>("");
  const [wasteRecycled, setWasteRecycled] = useState<string>("");
  const [socialImpact, setSocialImpact] = useState<string>("");

  useEffect(() => {
    esgApi.metrics().then((data) => {
      setMetrics(data);
      setRenewableEnergy(String(data.renewable_energy_percent));
      setCarbonIntensity(String(data.carbon_intensity));
      setWasteRecycled(String(data.waste_recycled_percent));
      setSocialImpact(String(data.social_impact_score));
    }).catch(() => {
      setMetrics({
        renewable_energy_percent: 0,
        carbon_intensity: 0,
        compliance_score: 0,
        waste_recycled_percent: 0,
        social_impact_score: 0,
      });
    });
  }, []);

  const handleUpdate = async () => {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      const updated = await esgApi.updateMetrics({
        renewable_energy_percent: parseFloat(renewableEnergy) || 0,
        carbon_intensity: parseFloat(carbonIntensity) || 0,
        waste_recycled_percent: parseFloat(wasteRecycled) || 0,
        social_impact_score: parseFloat(socialImpact) || 0,
      });
      setMetrics(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setSaveError(err?.message ?? "Failed to save ESG metrics");
    } finally {
      setSaving(false);
    }
  };

  const ESG_DETAILS = metrics
    ? [
        { label: "Renewable Energy", value: metrics.renewable_energy_percent, icon: Wind, color: "text-indigo-primary", bg: "bg-indigo-primary/10", unit: "%" },
        { label: "Carbon Intensity", value: metrics.carbon_intensity, icon: Leaf, color: "text-cyan-accent", bg: "bg-cyan-accent/10", unit: "tCO2e" },
        { label: "Waste Recycled", value: metrics.waste_recycled_percent, icon: Recycle, color: "text-indigo-primary", bg: "bg-indigo-primary/10", unit: "%" },
        { label: "Social Impact", value: metrics.social_impact_score, icon: Users, color: "text-cyan-accent", bg: "bg-cyan-accent/10", unit: "/100" },
      ]
    : [];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-soft">ESG Insights</h1>
          <p className="text-slate-muted">Detailed breakdown of your environmental and social performance.</p>
        </div>
        <Badge variant="success" className="h-fit px-4 py-1.5 text-sm">
          Top 5% in Industry
        </Badge>
      </div>

      {/* ESG Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {ESG_DETAILS.map((item, i) => (
          <Card key={i} className="group hover:border-indigo-primary/30 transition-all">
            <div className="mb-4 flex items-center justify-between">
              <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl", item.bg)}>
                <item.icon className={cn("h-5 w-5", item.color)} />
              </div>
              <TrendingUp className="h-4 w-4 text-indigo-primary" />
            </div>
            <p className="text-sm text-slate-muted">{item.label}</p>
            <div className="flex items-baseline gap-1">
              <p className="text-2xl font-bold text-slate-soft">{item.value}</p>
              <span className="text-sm text-slate-muted">{item.unit}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Update Form */}
      <Card>
        <h3 className="mb-6 text-lg font-bold text-slate-soft">Update ESG Metrics</h3>
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-medium uppercase tracking-wider text-slate-muted">Renewable Energy (%)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={renewableEnergy}
              onChange={(e) => setRenewableEnergy(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium uppercase tracking-wider text-slate-muted">Carbon Intensity (tCO2e)</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={carbonIntensity}
              onChange={(e) => setCarbonIntensity(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium uppercase tracking-wider text-slate-muted">Waste Recycled (%)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={wasteRecycled}
              onChange={(e) => setWasteRecycled(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium uppercase tracking-wider text-slate-muted">Social Impact Score (/100)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={socialImpact}
              onChange={(e) => setSocialImpact(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50"
            />
          </div>
        </div>
        <div className="mt-6 flex items-center gap-4">
          <Button onClick={handleUpdate} disabled={saving}>
            {saving ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving…</>
            ) : (
              "Save Metrics"
            )}
          </Button>
          {saveSuccess && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 text-sm text-green-400"
            >
              <CheckCircle2 className="h-4 w-4" />
              Metrics updated successfully
            </motion.div>
          )}
          {saveError && <p className="text-sm text-red-400">{saveError}</p>}
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Industry Benchmark */}
        <Card className="lg:col-span-2">
          <h3 className="mb-6 text-lg font-bold text-slate-soft">Industry Benchmarking</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={BENCHMARK_DATA} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" horizontal={false} />
                <XAxis type="number" hide />
                <YAxis 
                  dataKey="category" 
                  type="category" 
                  stroke="#94A3B8" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <Tooltip 
                  cursor={{ fill: '#ffffff05' }}
                  contentStyle={{ backgroundColor: '#0F172A', border: '1px solid #ffffff10', borderRadius: '12px' }}
                />
                <Bar dataKey="yourScore" name="Your Score" fill="#6366F1" radius={[0, 4, 4, 0]} barSize={20} />
                <Bar dataKey="industryAvg" name="Industry Average" fill="#ffffff10" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Improvement Suggestions */}
        <Card>
          <h3 className="mb-6 text-lg font-bold text-slate-soft">Improvement Areas</h3>
          <div className="space-y-4">
            {[
              { title: "Waste Management", desc: "Increase recycling rate by 15% to unlock 0.2% rate discount.", impact: "High" },
              { title: "Supply Chain", desc: "Onboard 2 more green-certified vendors.", impact: "Medium" },
              { title: "Data Transparency", desc: "Submit quarterly ESG audit for higher trust score.", impact: "Low" },
            ].map((item, i) => (
              <div key={i} className="rounded-xl bg-white/5 p-4 border border-white/5 hover:border-indigo-primary/20 transition-all">
                <div className="mb-1 flex items-center justify-between">
                  <p className="font-semibold text-slate-soft">{item.title}</p>
                  <Badge variant={item.impact === "High" ? "success" : "default"}>{item.impact}</Badge>
                </div>
                <p className="text-xs text-slate-muted">{item.desc}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Compliance Section */}
      <Card className="border-indigo-primary/20 bg-indigo-primary/5">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-primary/20 text-indigo-primary">
              <ShieldCheck className="h-7 w-7" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-soft">Compliance Status: Verified</h3>
              <p className="text-sm text-slate-muted">All regulatory ESG filings are up to date as of April 2026.</p>
            </div>
          </div>
          <Button variant="outline" size="sm">View Certificates</Button>
        </div>
      </Card>
    </div>
  );
}
