import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Leaf, ArrowRight, Mail, Lock, User, Building2, Zap, ShieldCheck, Globe } from "lucide-react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Button, Card, Badge } from "../components/UI";
import { useAuth } from "../context/AuthContext";
import { cn } from "../lib/utils";

export function AuthPages() {
  const [isLogin, setIsLogin] = useState(true);
  const [role, setRole] = useState<'BORROWER' | 'LENDER'>('BORROWER');
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: ""
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, signup, authError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/dashboard";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (isLogin) {
        await login({ email: formData.email, password: formData.password });
      } else {
        await signup({
          name: formData.name,
          email: formData.email,
          password: formData.password,
          role,
        });
      }
      navigate(from, { replace: true });
    } catch {
      // authError is set by the context; do not navigate
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-black font-sans text-slate-soft selection:bg-indigo-primary/30">
      {/* Back to Home Button */}
      <div className="absolute left-6 top-6 z-20">
        <Link 
          to="/" 
          className="flex items-center gap-2 rounded-full bg-white/5 px-4 py-2 text-sm font-medium text-slate-muted transition-all hover:bg-white/10 hover:text-slate-soft border border-white/10"
        >
          <ArrowRight className="h-4 w-4 rotate-180" />
          Back to Home
        </Link>
      </div>

      {/* Background Effects matching Landing Page */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-black/80" />
        <div className="absolute top-[30%] left-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-primary/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[400px] w-[400px] rounded-full bg-cyan-accent/5 blur-[100px]" />
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:40px_40px]" />
      </div>

      <div className="relative z-10 w-full max-w-5xl px-6 py-12">
        <div className="grid gap-16 lg:grid-cols-2 lg:items-center">
          {/* Left Side: Branding & Value Prop */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="hidden lg:block"
          >
            <Link to="/" className="mb-12 flex items-center gap-3 group">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-primary to-cyan-accent shadow-lg shadow-indigo-primary/20 transition-transform group-hover:scale-110">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold tracking-tight text-slate-soft">JUST THRYVE</span>
            </Link>

            <h1 className="mb-8 text-5xl font-bold leading-tight text-slate-soft">
              The Future of <br />
              <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-indigo-400 bg-clip-text text-transparent">
                Sustainable Credit
              </span>
            </h1>

            <div className="space-y-8">
              {[
                { title: "OCEN Enabled", desc: "Access the Open Credit Enablement Network protocol.", icon: Zap },
                { title: "ESG Verified", desc: "Get rewarded for your sustainability impact.", icon: ShieldCheck },
                { title: "Flow-Based", desc: "Real-time underwriting based on your revenue flow.", icon: Globe },
              ].map((item, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.1 }}
                  className="flex gap-4"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/5 text-indigo-primary">
                    <item.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-soft">{item.title}</h4>
                    <p className="text-sm text-slate-muted">{item.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right Side: Auth Form */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="mx-auto w-full max-w-md"
          >
            <div className="mb-8 text-center lg:hidden">
              <Link to="/" className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-primary shadow-lg shadow-indigo-primary/20">
                <Zap className="h-7 w-7 text-white" />
              </Link>
              <h2 className="text-3xl font-bold text-slate-soft">
                {isLogin ? "Welcome Back" : "Create Account"}
              </h2>
            </div>

            <Card className="relative overflow-hidden border-white/10 bg-white/[0.02] p-8 backdrop-blur-xl">
              <div className="mb-8">
                <h3 className="mb-2 text-xl font-bold text-slate-soft">
                  {isLogin ? "Sign In" : "Get Started"}
                </h3>
                <p className="text-sm text-slate-muted">
                  {isLogin ? "Enter your credentials to access your dashboard" : "Join 1,200+ SMEs scaling with JUST THRYVE"}
                </p>
              </div>

              <div className="mb-8 grid grid-cols-2 gap-2 rounded-xl bg-black/40 p-1">
                <button
                  type="button"
                  onClick={() => setRole('BORROWER')}
                  className={cn(
                    "flex items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium transition-all",
                    role === 'BORROWER' ? "bg-indigo-primary text-white shadow-lg shadow-indigo-primary/20" : "text-slate-muted hover:text-slate-soft"
                  )}
                >
                  <User className="h-4 w-4" />
                  Borrower
                </button>
                <button
                  type="button"
                  onClick={() => setRole('LENDER')}
                  className={cn(
                    "flex items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium transition-all",
                    role === 'LENDER' ? "bg-indigo-primary text-white shadow-lg shadow-indigo-primary/20" : "text-slate-muted hover:text-slate-soft"
                  )}
                >
                  <Building2 className="h-4 w-4" />
                  Lender
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <AnimatePresence mode="wait">
                  {!isLogin && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-2"
                    >
                      <label className="text-xs font-semibold uppercase tracking-wider text-slate-muted">Full Name</label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-muted" />
                        <input
                          type="text"
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                          required={!isLogin}
                          className="w-full rounded-xl bg-white/5 py-3 pl-10 pr-4 text-slate-soft outline-none ring-1 ring-white/10 transition-all focus:ring-indigo-primary/50"
                          placeholder="John Doe"
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-slate-muted">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-muted" />
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full rounded-xl bg-white/5 py-3 pl-10 pr-4 text-slate-soft outline-none ring-1 ring-white/10 transition-all focus:ring-indigo-primary/50"
                      placeholder="name@company.com"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-slate-muted">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-muted" />
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                      className="w-full rounded-xl bg-white/5 py-3 pl-10 pr-4 text-slate-soft outline-none ring-1 ring-white/10 transition-all focus:ring-indigo-primary/50"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                <Button type="submit" className="h-12 w-full shadow-lg shadow-indigo-500/20" disabled={isSubmitting}>
                  {isSubmitting ? "Please wait…" : (isLogin ? "Sign In" : "Create Account")}
                  {!isSubmitting && <ArrowRight className="ml-2 h-5 w-5" />}
                </Button>

                {authError && (
                  <p className="mt-3 rounded-lg bg-red-500/10 px-4 py-2 text-center text-sm text-red-400">
                    {authError}
                  </p>
                )}
              </form>

              <div className="mt-8 text-center">
                <button
                  type="button"
                  onClick={() => setIsLogin(!isLogin)}
                  className="text-sm text-slate-muted transition-colors hover:text-indigo-primary"
                >
                  {isLogin ? (
                    <>Don't have an account? <span className="font-bold text-indigo-primary">Sign up</span></>
                  ) : (
                    <>Already have an account? <span className="font-bold text-indigo-primary">Sign in</span></>
                  )}
                </button>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
