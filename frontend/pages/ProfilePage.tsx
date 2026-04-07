import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { 
  User, 
  Mail, 
  Building2, 
  Phone, 
  MapPin, 
  Camera,
  Shield,
  Bell,
  Lock,
  CreditCard,
  CheckCircle2,
  Leaf
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useESG } from "../context/ESGContext";
import { Card, Button, Badge } from "../components/UI";
import { authApi } from "../services/api";
import { cn } from "../lib/utils";

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const { score: ecsScore } = useESG();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'notifications'>('profile');
  const [logo, setLogo] = useState<string | null>(null);
  const [name, setName] = useState(user?.name ?? "");
  const [businessName, setBusinessName] = useState(user?.businessName ?? "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      await authApi.updateProfile({ name, business_name: businessName });
      await refreshUser();
    } catch (err: any) {
      setSaveError(err?.message ?? "Failed to save changes");
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogo(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile Details', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-end gap-6">
        <div className="relative group">
          <div className="h-32 w-32 rounded-3xl bg-gradient-to-br from-indigo-primary to-cyan-accent p-1 shadow-xl shadow-indigo-primary/20">
            <div className="h-full w-full rounded-[22px] bg-app-bg flex items-center justify-center overflow-hidden">
              {logo ? (
                <img src={logo} alt="Company Logo" className="h-full w-full object-cover" />
              ) : (
                <User className="h-16 w-16 text-indigo-primary" />
              )}
            </div>
          </div>
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleLogoUpload}
            className="hidden" 
            accept="image/*"
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="absolute -bottom-2 -right-2 p-2 rounded-xl bg-indigo-primary text-white shadow-lg hover:scale-110 transition-transform"
          >
            <Camera className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 space-y-1">
          <h1 className="text-3xl font-bold text-slate-soft">{user?.name}</h1>
          <p className="text-slate-muted font-medium">{user?.businessName}</p>
          <div className="flex items-center gap-2 pt-2">
            <Badge variant="success" className="bg-indigo-primary/10 text-indigo-primary border-indigo-primary/20">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Verified Business
            </Badge>
            <Badge variant="default" className="bg-white/5 text-slate-muted border-white/10">
              {user?.role === 'borrower' ? 'SME Borrower' : 'Lender'}
            </Badge>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm">Edit Profile</Button>
          <Button size="sm" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save Changes"}
          </Button>
        </div>
      </div>
      {saveError && (
        <p className="text-sm text-red-400">{saveError}</p>
      )}

      <div className="flex gap-1 p-1 rounded-2xl bg-white/5 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              "flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-medium transition-all",
              activeTab === tab.id 
                ? "bg-indigo-primary text-white shadow-lg shadow-indigo-primary/20" 
                : "text-slate-muted hover:text-slate-soft"
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <AnimatePresence mode="wait">
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                <Card className="p-6 space-y-6">
                  <h3 className="text-lg font-bold text-slate-soft">Business Information</h3>
                  <div className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-slate-muted uppercase tracking-wider">Business Name</label>
                      <div className="relative">
                        <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-muted" />
                        <input 
                          type="text" 
                          value={businessName}
                          onChange={(e) => setBusinessName(e.target.value)}
                          className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-slate-muted uppercase tracking-wider">Email Address</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-muted" />
                        <input 
                          type="email" 
                          defaultValue={user?.email}
                          readOnly
                          className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50 opacity-60 cursor-not-allowed"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-slate-muted uppercase tracking-wider">Phone Number</label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-muted" />
                        <input 
                          type="tel" 
                          defaultValue="+91 98765 43210"
                          className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-slate-muted uppercase tracking-wider">Location</label>
                      <div className="relative">
                        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-muted" />
                        <input 
                          type="text" 
                          defaultValue="Bangalore, India"
                          className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-slate-soft outline-none focus:ring-1 focus:ring-indigo-primary/50"
                        />
                      </div>
                    </div>
                  </div>
                </Card>

                <Card className="p-6 space-y-6">
                  <h3 className="text-lg font-bold text-slate-soft">Financial Integration</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-xl bg-indigo-primary/10 flex items-center justify-center text-indigo-primary">
                          <CreditCard className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold text-slate-soft">GST Integration</p>
                          <p className="text-xs text-slate-muted">Connected to GST portal via OCEN</p>
                        </div>
                      </div>
                      <Badge variant="success">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-xl bg-cyan-accent/10 flex items-center justify-center text-cyan-accent">
                          <Building2 className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-bold text-slate-soft">Bank Account</p>
                          <p className="text-xs text-slate-muted">HDFC Bank •••• 4242</p>
                        </div>
                      </div>
                      <Badge variant="success">Active</Badge>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {activeTab === 'security' && (
              <motion.div
                key="security"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                <Card className="p-6 space-y-6">
                  <h3 className="text-lg font-bold text-slate-soft">Security Settings</h3>
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-bold text-slate-soft">Two-Factor Authentication</p>
                        <p className="text-sm text-slate-muted">Add an extra layer of security to your account.</p>
                      </div>
                      <button className="h-6 w-11 rounded-full bg-indigo-primary relative transition-colors">
                        <div className="absolute right-1 top-1 h-4 w-4 rounded-full bg-white" />
                      </button>
                    </div>
                    <div className="pt-6 border-t border-white/5">
                      <Button variant="outline" className="w-full justify-start">
                        <Lock className="h-4 w-4 mr-2" />
                        Change Password
                      </Button>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="space-y-6">
          <Card className="p-6 bg-indigo-primary/5 border-indigo-primary/20">
            <h4 className="font-bold text-slate-soft mb-2">ESG Verification</h4>
            <p className="text-sm text-slate-muted mb-4">Your business is currently verified for ESG-linked credit. Maintain your score to keep low-interest offers.</p>
            <div className="flex items-center gap-2 text-indigo-primary font-bold">
              <Leaf className="h-4 w-4" />
              <span>Score: {ecsScore}</span>
            </div>
          </Card>
          
          <Card className="p-6">
            <h4 className="font-bold text-slate-soft mb-4">Account Status</h4>
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-slate-muted">Member Since</span>
                <span className="text-slate-soft">Oct 2025</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-muted">Last Login</span>
                <span className="text-slate-soft">2 hours ago</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-muted">Account Type</span>
                <span className="text-indigo-primary font-medium">Premium</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

