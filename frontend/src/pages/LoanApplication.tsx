import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { 
  Building2, 
  FileText, 
  Leaf, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft,
  Upload,
  Zap,
  ShieldCheck,
  X,
  Loader2
} from "lucide-react";
import { Card, Button, Badge } from "../components/UI";
import { cn } from "../lib/utils";
import { loansApi, ApiError } from "../services/api";

const STEPS = [
  { id: 1, title: "Business Details", icon: Building2 },
  { id: 2, title: "Financial Data", icon: FileText },
  { id: 3, title: "ESG Assessment", icon: Leaf },
  { id: 4, title: "Review & Submit", icon: CheckCircle2 },
];

import { useNavigate } from "react-router-dom";

export function LoanApplication() {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [companySize, setCompanySize] = useState("");
  const [annualRevenue, setAnnualRevenue] = useState("");
  const [loanAmount, setLoanAmount] = useState("");
  const [loanPurpose, setLoanPurpose] = useState("Business Expansion");
  const [tenureMonths, setTenureMonths] = useState("12");
  const [uploadedFiles, setUploadedFiles] = useState<{ id: string; name: string; size: string; progress: number; status: 'uploading' | 'completed' | 'error' }[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newFiles = Array.from(files).map((file: File) => ({
      id: Math.random().toString(36).substring(7),
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + " MB",
      progress: 0,
      status: 'uploading' as const
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);

    newFiles.forEach(file => {
      simulateUpload(file.id);
    });
  };

  const simulateUpload = (id: string) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 30;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setUploadedFiles(prev => prev.map(f => f.id === id ? { ...f, progress: 100, status: 'completed' } : f));
      } else {
        setUploadedFiles(prev => prev.map(f => f.id === id ? { ...f, progress } : f));
      }
    }, 500);
  };

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id));
  };

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, STEPS.length));
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 1));

  const handleSubmit = async () => {
    const amount = parseFloat(loanAmount.replace(/,/g, '')) || 0;
    if (!amount) {
      setSubmitError("Please enter a valid loan amount.");
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const { loan_id } = await loansApi.apply({
        amount_requested: amount,
        purpose: loanPurpose || "Business Expansion",
        tenure_months: parseInt(tenureMonths) || 12,
      });
      await loansApi.submit(loan_id);
      setIsSuccess(true);
      setTimeout(() => navigate(`/dashboard/offers?loanId=${loan_id}`), 2000);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : (err instanceof Error ? err.message : "Submission failed. Please try again.");
      setSubmitError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-indigo-primary/20 text-indigo-primary"
        >
          <CheckCircle2 className="h-12 w-12" />
        </motion.div>
        <h2 className="mb-2 text-3xl font-bold text-slate-soft">Application Submitted!</h2>
        <p className="mb-8 max-w-md text-slate-muted">
          Your loan application is being processed by our AI underwriting engine. 
          Redirecting to your offers…
        </p>
        <Button onClick={() => navigate("/dashboard")}>Back to Dashboard</Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-soft">Apply for ESG-Linked Loan</h1>
        <p className="text-slate-muted">Complete the steps below to unlock flow-based credit.</p>
      </div>

      {/* Progress Bar */}
      <div className="relative flex justify-between">
        <div className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-white/5" />
        <div 
          className="absolute left-0 top-1/2 h-0.5 -translate-y-1/2 bg-indigo-primary transition-all duration-500" 
          style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
        />
        {STEPS.map((step) => (
          <div key={step.id} className="relative z-10 flex flex-col items-center gap-2">
            <div className={cn(
              "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300",
              currentStep >= step.id 
                ? "border-indigo-primary bg-indigo-primary text-white" 
                : "border-white/10 bg-navy-deep text-slate-muted"
            )}>
              <step.icon className="h-5 w-5" />
            </div>
            <span className={cn(
              "text-xs font-medium transition-colors",
              currentStep >= step.id ? "text-indigo-primary" : "text-slate-muted"
            )}>
              {step.title}
            </span>
          </div>
        ))}
      </div>

      {/* Form Content */}
      <Card className="min-h-[400px] border-white/5">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {currentStep === 1 && (
              <div className="grid gap-6">
                <h3 className="text-xl font-bold text-slate-soft">Business Information</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Business Name</label>
                    <input type="text" className="w-full rounded-xl bg-white/5 p-3 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50" placeholder="EcoCorp Manufacturing" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">GST Number</label>
                    <input type="text" className="w-full rounded-xl bg-white/5 p-3 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50" placeholder="27AAAAA0000A1Z5" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Industry Type</label>
                    <select className="w-full rounded-xl bg-navy-deep p-3 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50">
                      <option>Manufacturing</option>
                      <option>Renewable Energy</option>
                      <option>Agri-tech</option>
                      <option>Waste Management</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Years in Business</label>
                    <input type="number" className="w-full rounded-xl bg-white/5 p-3 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50" placeholder="5" />
                  </div>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="grid gap-8">
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold text-slate-soft font-display">Financial Data</h3>
                  <p className="text-sm text-slate-muted">Secure verification via OCEN protocols</p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-slate-muted">Average Monthly Revenue</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-muted">₹</span>
                      <input type="text" className="w-full rounded-2xl bg-white/5 p-4 pl-8 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50 transition-all" placeholder="5,00,000" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-slate-muted">Requested Loan Amount (₹)</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-muted">₹</span>
                      <input
                        type="text"
                        className="w-full rounded-2xl bg-white/5 p-4 pl-8 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50 transition-all"
                        placeholder="25,00,000"
                        value={loanAmount}
                        onChange={(e) => setLoanAmount(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-slate-muted">Loan Purpose</label>
                    <input
                      type="text"
                      className="w-full rounded-2xl bg-white/5 p-4 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50 transition-all"
                      placeholder="Business Expansion"
                      value={loanPurpose}
                      onChange={(e) => setLoanPurpose(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-slate-muted">Tenure (Months)</label>
                    <select
                      className="w-full rounded-2xl bg-navy-deep p-4 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50 transition-all"
                      value={tenureMonths}
                      onChange={(e) => setTenureMonths(e.target.value)}
                    >
                      <option value="6">6 months</option>
                      <option value="12">12 months</option>
                      <option value="18">18 months</option>
                      <option value="24">24 months</option>
                      <option value="36">36 months</option>
                    </select>
                  </div>
                </div>

                <div className="rounded-2xl border border-indigo-primary/20 bg-indigo-primary/5 p-6 backdrop-blur-sm">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-primary text-white shadow-lg shadow-indigo-500/20">
                      <Zap className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-bold text-slate-soft">Instant GST Verification</p>
                      <p className="text-sm text-slate-muted leading-relaxed">Connect your GST portal to automatically verify revenue flows. This significantly improves your approval odds and reduces interest rates.</p>
                      <Button variant="outline" size="sm" className="mt-4 rounded-full border-indigo-primary/30 text-indigo-primary hover:bg-indigo-primary/10">
                        Connect GST Portal
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="text-xs font-bold uppercase tracking-widest text-slate-muted">Supporting Documents</label>
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="group relative cursor-pointer overflow-hidden rounded-[2rem] border-2 border-dashed border-white/10 bg-white/5 p-12 text-center transition-all hover:border-indigo-primary/50 hover:bg-indigo-primary/5"
                  >
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      onChange={handleFileSelect} 
                      multiple 
                      className="hidden" 
                      accept=".pdf,.json,.jpg,.png"
                    />
                    <div className="flex flex-col items-center gap-4">
                      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-primary/10 text-indigo-primary transition-all group-hover:scale-110 group-hover:bg-indigo-primary group-hover:text-white group-hover:rotate-6">
                        <Upload className="h-8 w-8" />
                      </div>
                      <div>
                        <p className="text-lg font-bold text-slate-soft">Drop your files here</p>
                        <p className="text-sm text-slate-muted mt-1">GST Returns, Bank Statements, or ESG Certifications</p>
                        <p className="text-[10px] text-indigo-primary/60 mt-2 uppercase tracking-widest font-bold">PDF, JSON, PNG up to 10MB</p>
                      </div>
                    </div>
                  </div>

                  {/* File List */}
                  <div className="grid gap-3 sm:grid-cols-2">
                    <AnimatePresence>
                      {uploadedFiles.map((file) => (
                        <motion.div
                          key={file.id}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                          className="group relative flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 transition-all hover:border-indigo-primary/30"
                        >
                          <div className={cn(
                            "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-colors",
                            file.status === 'completed' ? "bg-emerald-400/10 text-emerald-400" : "bg-indigo-primary/10 text-indigo-primary"
                          )}>
                            {file.status === 'uploading' ? <Loader2 className="h-6 w-6 animate-spin" /> : <FileText className="h-6 w-6" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-sm font-bold text-slate-soft truncate pr-2">{file.name}</p>
                              <button 
                                onClick={(e) => { e.stopPropagation(); removeFile(file.id); }}
                                className="opacity-0 group-hover:opacity-100 p-1 text-slate-muted hover:text-rose-400 transition-all"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="relative h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                                <motion.div 
                                  initial={{ width: 0 }}
                                  animate={{ width: `${file.progress}%` }}
                                  className={cn(
                                    "absolute left-0 top-0 h-full transition-colors",
                                    file.status === 'completed' ? "bg-emerald-400" : "bg-indigo-primary"
                                  )}
                                />
                              </div>
                              <span className="text-[10px] font-black text-slate-muted uppercase">{Math.round(file.progress)}%</span>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 3 && (
              <div className="grid gap-6">
                <h3 className="text-xl font-bold text-slate-soft">ESG Assessment</h3>
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Company Size (Employees)</label>
                    <input 
                      type="number" 
                      className="w-full rounded-xl bg-white/5 p-3 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50" 
                      placeholder="50"
                      value={companySize}
                      onChange={(e) => setCompanySize(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Annual Revenue (INR)</label>
                    <input 
                      type="number" 
                      className="w-full rounded-xl bg-white/5 p-3 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50" 
                      placeholder="10000000"
                      value={annualRevenue}
                      onChange={(e) => setAnnualRevenue(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Renewable Energy Usage (%)</label>
                    <input type="range" className="w-full accent-indigo-primary" min="0" max="100" />
                    <div className="flex justify-between text-xs text-slate-muted">
                      <span>0%</span>
                      <span>100%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Waste Recycled (%)</label>
                    <input type="range" className="w-full accent-indigo-primary" min="0" max="100" />
                    <div className="flex justify-between text-xs text-slate-muted">
                      <span>0%</span>
                      <span>100%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Carbon Footprint (Annual Tons)</label>
                    <input type="number" className="w-full rounded-xl bg-white/5 p-3 text-slate-soft outline-none ring-1 ring-white/10 focus:ring-indigo-primary/50" placeholder="12.5" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Electric Vehicle Fleet (%)</label>
                    <input type="range" className="w-full accent-indigo-primary" min="0" max="100" />
                    <div className="flex justify-between text-xs text-slate-muted">
                      <span>0%</span>
                      <span>100%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-slate-muted">Compliance Certifications</label>
                    <div className="flex flex-wrap gap-2">
                      {["ISO 14001", "LEED", "B-Corp", "GRI"].map(cert => (
                        <button key={cert} className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-muted hover:bg-indigo-primary/20 hover:border-indigo-primary/50 hover:text-indigo-primary transition-colors">
                          {cert}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 4 && (
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-slate-soft">Review Application</h3>
                <div className="rounded-2xl bg-white/5 p-6 space-y-4">
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-muted">Business</span>
                    <span className="font-medium text-slate-soft">EcoCorp Manufacturing</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-muted">Loan Amount</span>
                    <span className="font-medium text-slate-soft">₹ 25,00,000</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-slate-muted">ESG Score Estimate</span>
                    <span className="font-medium text-indigo-primary">845 / 1000</span>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-xl bg-indigo-primary/10 p-4 text-indigo-primary">
                  <ShieldCheck className="mt-1 h-5 w-5" />
                  <p className="text-sm">
                    By submitting, you agree to the blockchain-based audit trail and real-time data sharing via OCEN protocols.
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="mt-12 flex flex-col gap-3">
          {submitError && (
            <p className="text-sm text-red-400 text-center">{submitError}</p>
          )}
          <div className="flex justify-between">
          <Button 
            variant="ghost" 
            onClick={prevStep} 
            disabled={currentStep === 1 || isSubmitting}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          
          {currentStep === STEPS.length ? (
            <Button 
              onClick={handleSubmit} 
              loading={isSubmitting}
              className="px-10"
            >
              Submit Application
            </Button>
          ) : (
            <Button onClick={nextStep}>
              Next Step
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
          </div>
        </div>
      </Card>
    </div>
  );
}
