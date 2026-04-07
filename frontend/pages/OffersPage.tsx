import { motion, AnimatePresence } from "motion/react";
import { 
  ShieldCheck, 
  TrendingDown, 
  Calendar, 
  Leaf,
  Scale,
  X,
  ArrowRight,
  Filter,
  ArrowUpDown,
  ChevronDown,
  Loader2,
  AlertCircle,
  Building2,
} from "lucide-react";
import { useState, useMemo, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Card, Button } from "../components/UI";
import { cn } from "../lib/utils";
import { loanService } from "../services/loanService";
import { OfferResponse } from "../services/api";

type SortKey = 'interest_rate' | 'offered_amount' | 'none';
type SortOrder = 'asc' | 'desc';

export function OffersPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const loanId = searchParams.get("loanId") ?? "";

  const [offers, setOffers] = useState<OfferResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [acceptingId, setAcceptingId] = useState<string | null>(null);
  const [acceptedId, setAcceptedId] = useState<string | null>(null);

  const [selectedOffers, setSelectedOffers] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [sortBy, setSortBy] = useState<SortKey>('none');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [minAmount, setMinAmount] = useState<number>(0);
  const [maxInterestRate, setMaxInterestRate] = useState<number>(20);

  useEffect(() => {
    if (!loanId) return;
    setLoading(true);
    setError(null);
    loanService.getOffers(loanId)
      .then(setOffers)
      .catch((err) => setError(err?.message ?? "Failed to load offers"))
      .finally(() => setLoading(false));
  }, [loanId]);

  const handleAcceptOffer = async (offerId: string) => {
    if (!loanId) return;
    setAcceptingId(offerId);
    try {
      await loanService.acceptOffer(loanId, offerId);
      setAcceptedId(offerId);
      setOffers((prev) =>
        prev.map((o) =>
          o.id === offerId
            ? { ...o, status: "accepted" }
            : o.status === "pending"
            ? { ...o, status: "rejected" }
            : o
        )
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to accept offer";
      setError(msg);
    } finally {
      setAcceptingId(null);
    }
  };

  const toggleOfferSelection = (id: string) => {
    setSelectedOffers(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const filteredAndSortedOffers = useMemo(() => {
    let result = [...offers];

    result = result.filter(offer =>
      offer.offered_amount >= minAmount &&
      offer.interest_rate <= maxInterestRate
    );

    if (sortBy !== 'none') {
      result.sort((a, b) => {
        const valA = a[sortBy] as number;
        const valB = b[sortBy] as number;
        if (sortOrder === 'asc') return valA - valB;
        return valB - valA;
      });
    }

    return result;
  }, [offers, sortBy, sortOrder, minAmount, maxInterestRate]);

  const selectedData = offers.filter(o => selectedOffers.includes(o.id));

  const getBestValue = (key: keyof OfferResponse, type: 'min' | 'max') => {
    if (selectedData.length < 2) return null;
    const values = selectedData.map(o => o[key] as number);
    return type === 'min' ? Math.min(...values) : Math.max(...values);
  };

  return (
    <div className="space-y-8 pb-24">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-soft">Lender Offers</h1>
          <p className="text-slate-muted">
            {loading
              ? "Loading offers…"
              : `We've found ${filteredAndSortedOffers.length} offer${filteredAndSortedOffers.length !== 1 ? "s" : ""} for your loan.`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {!loanId && (
            <Button variant="outline" size="sm" onClick={() => navigate("/dashboard")}>
              Select a Loan First
            </Button>
          )}
          {selectedOffers.length > 0 && (
            <Button 
              variant="secondary" 
              size="sm" 
              onClick={() => setShowComparison(true)}
              disabled={selectedOffers.length < 2}
            >
              <Scale className="mr-2 h-4 w-4" />
              Compare {selectedOffers.length} Offers
            </Button>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-primary" />
        </div>
      )}

      {/* No loanId prompt */}
      {!loading && !loanId && (
        <div className="py-20 text-center">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-white/5 text-zinc-500 mb-4">
            <Building2 className="h-8 w-8" />
          </div>
          <h3 className="text-xl font-bold text-white">No Loan Selected</h3>
          <p className="text-zinc-400 mb-4">Navigate here from a loan in "Offers Received" status.</p>
          <Button variant="ghost" onClick={() => navigate("/dashboard")}>Go to Dashboard</Button>
        </div>
      )}

      {/* Accepted banner */}
      {acceptedId && (
        <div className="flex items-center gap-3 rounded-xl border border-green-500/20 bg-green-500/10 px-4 py-3 text-sm text-green-400">
          Offer accepted successfully! Your loan is now in "accepted" status.
        </div>
      )}

      {!loading && loanId && (
        <>
          {/* Filter Bar */}
          <Card className="bg-white/5 border-white/10 p-4">
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-indigo-primary" />
                <span className="text-sm font-medium text-slate-muted">Filters:</span>
              </div>

              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-muted uppercase tracking-wider">Min Amount</label>
                  <select 
                    value={minAmount}
                    onChange={(e) => setMinAmount(Number(e.target.value))}
                    className="bg-navy-deep border border-white/10 rounded-lg px-3 py-1.5 text-sm text-slate-soft focus:outline-none focus:ring-1 focus:ring-indigo-primary/50"
                  >
                    <option value={0}>Any</option>
                    <option value={500000}>₹5L+</option>
                    <option value={1000000}>₹10L+</option>
                    <option value={2000000}>₹20L+</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-muted uppercase tracking-wider">Max Interest Rate</label>
                  <select 
                    value={maxInterestRate}
                    onChange={(e) => setMaxInterestRate(Number(e.target.value))}
                    className="bg-navy-deep border border-white/10 rounded-lg px-3 py-1.5 text-sm text-slate-soft focus:outline-none focus:ring-1 focus:ring-indigo-primary/50"
                  >
                    <option value={20}>Any</option>
                    <option value={12}>Under 12%</option>
                    <option value={10}>Under 10%</option>
                    <option value={9}>Under 9%</option>
                  </select>
                </div>

                <div className="h-6 w-px bg-white/10 mx-2" />

                <div className="flex items-center gap-2">
                  <ArrowUpDown className="h-4 w-4 text-indigo-primary" />
                  <label className="text-xs text-slate-muted uppercase tracking-wider">Sort By</label>
                  <select 
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as SortKey)}
                    className="bg-navy-deep border border-white/10 rounded-lg px-3 py-1.5 text-sm text-slate-soft focus:outline-none focus:ring-1 focus:ring-indigo-primary/50"
                  >
                    <option value="none">Default</option>
                    <option value="interest_rate">Interest Rate</option>
                    <option value="offered_amount">Offered Amount</option>
                  </select>
                  {sortBy !== 'none' && (
                    <button 
                      onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                      className="p-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-muted hover:text-slate-soft transition-colors"
                    >
                      <ChevronDown className={cn("h-4 w-4 transition-transform", sortOrder === 'desc' ? "rotate-180" : "")} />
                    </button>
                  )}
                </div>
              </div>

              <button 
                onClick={() => {
                  setSortBy('none');
                  setSortOrder('asc');
                  setMinAmount(0);
                  setMaxInterestRate(20);
                }}
                className="ml-auto text-xs font-medium text-slate-muted hover:text-indigo-primary transition-colors"
              >
                Reset All
              </button>
            </div>
          </Card>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredAndSortedOffers.map((offer) => {
              const isSelected = selectedOffers.includes(offer.id);
              const isAccepted = offer.status === "accepted";
              const isRejected = offer.status === "rejected";
              return (
                <Card 
                  key={offer.id} 
                  className={cn(
                    "group relative flex flex-col overflow-hidden border-white/5 transition-all",
                    isSelected ? "border-indigo-primary/50 ring-1 ring-indigo-primary/20" : "hover:border-indigo-primary/30",
                    isAccepted && "border-green-500/30 ring-1 ring-green-500/20",
                    isRejected && "opacity-50"
                  )}
                >
                  {offer.interest_rate < 10 && (
                    <div className="absolute -right-12 top-6 rotate-45 bg-indigo-primary px-12 py-1 text-[10px] font-bold text-white uppercase tracking-widest">
                      Best Rate
                    </div>
                  )}

                  <div className="absolute left-4 top-4 z-10">
                    <input 
                      type="checkbox" 
                      checked={isSelected}
                      onChange={() => toggleOfferSelection(offer.id)}
                      disabled={isAccepted || isRejected}
                      className="h-5 w-5 rounded border-white/10 bg-white/5 text-indigo-primary focus:ring-indigo-primary/50 disabled:opacity-40"
                    />
                  </div>
                  
                  <div className="mb-6 flex items-center gap-4 pl-8">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-primary/20 text-indigo-primary">
                      <Building2 className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-soft">Lender Offer</h3>
                      <div className="flex items-center gap-1 text-xs text-slate-muted">
                        <ShieldCheck className="h-3 w-3" />
                        Verified Lender
                      </div>
                    </div>
                  </div>

                  <div className="mb-8 grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <p className="text-xs text-slate-muted uppercase tracking-wider">Interest Rate</p>
                      <p className="text-2xl font-bold text-slate-soft">{offer.interest_rate}%</p>
                    </div>
                    <div className="space-y-1 text-right">
                      <p className="text-xs text-slate-muted uppercase tracking-wider">Offered Amount</p>
                      <p className="text-2xl font-bold text-indigo-primary">
                        ₹{(offer.offered_amount / 100000).toFixed(1)}L
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-slate-muted uppercase tracking-wider">Tenure</p>
                      <p className="text-lg font-semibold text-slate-soft">{offer.tenure_months} Months</p>
                    </div>
                    <div className="space-y-1 text-right">
                      <p className="text-xs text-slate-muted uppercase tracking-wider">Status</p>
                      <p className={cn(
                        "text-lg font-semibold capitalize",
                        isAccepted ? "text-green-400" : isRejected ? "text-red-400" : "text-cyan-accent"
                      )}>
                        {offer.status}
                      </p>
                    </div>
                  </div>

                  <div className="mb-6 space-y-3 rounded-xl bg-white/5 p-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-muted">Processing Fee</span>
                      <span className="text-slate-soft">0.5%</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-muted">Prepayment Penalty</span>
                      <span className="text-slate-soft">Nil</span>
                    </div>
                    <div className="flex items-center justify-between text-sm font-bold border-t border-white/5 pt-2">
                      <span className="text-slate-muted">Monthly EMI</span>
                      <span className="text-indigo-primary">₹{Number(offer.emi_amount).toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="mt-auto flex flex-col gap-3">
                    {isAccepted ? (
                      <Button className="w-full" disabled>
                        Offer Accepted ✓
                      </Button>
                    ) : isRejected ? (
                      <Button className="w-full" disabled variant="ghost">
                        Offer Rejected
                      </Button>
                    ) : (
                      <Button
                        className="w-full"
                        onClick={() => handleAcceptOffer(offer.id)}
                        disabled={acceptingId !== null || !!acceptedId}
                      >
                        {acceptingId === offer.id ? (
                          <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Accepting…</>
                        ) : (
                          "Accept Offer"
                        )}
                      </Button>
                    )}
                  </div>
                </Card>
              );
            })}
            {filteredAndSortedOffers.length === 0 && !loading && (
              <div className="col-span-full py-20 text-center">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-white/5 text-zinc-500 mb-4">
                  <Filter className="h-8 w-8" />
                </div>
                <h3 className="text-xl font-bold text-white">No offers found</h3>
                <p className="text-zinc-400">
                  {offers.length === 0
                    ? "No offers have been made for this loan yet."
                    : "Try adjusting your filters to see more results."}
                </p>
                {offers.length > 0 && (
                  <Button 
                    variant="ghost" 
                    className="mt-4"
                    onClick={() => {
                      setSortBy('none');
                      setSortOrder('asc');
                      setMinAmount(0);
                      setMaxInterestRate(20);
                    }}
                  >
                    Reset Filters
                  </Button>
                )}
              </div>
            )}
          </div>

          <Card className="bg-indigo-primary/5 border-indigo-primary/20">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-primary/20 text-indigo-primary">
                <Leaf className="h-6 w-6" />
              </div>
              <div>
                <h4 className="font-bold text-slate-soft">About ESG-Linked Offers</h4>
                <p className="text-sm text-slate-muted">
                  Lenders on JustThryve reward businesses with strong ESG credentials with lower interest 
                  rates and higher credit limits. Improve your ESG score to unlock better offers.
                </p>
              </div>
            </div>
          </Card>
        </>
      )}

      {/* Comparison Modal */}
      <AnimatePresence>
        {showComparison && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 md:p-8">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowComparison(false)}
              className="absolute inset-0 bg-zinc-950/80 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-5xl overflow-hidden rounded-3xl border border-white/10 bg-navy-deep shadow-2xl"
            >
              <div className="flex items-center justify-between border-b border-white/5 p-6">
                <div className="flex items-center gap-3">
                  <Scale className="h-6 w-6 text-indigo-primary" />
                  <h2 className="text-xl font-bold text-slate-soft">Compare Loan Offers</h2>
                </div>
                <button 
                  onClick={() => setShowComparison(false)}
                  className="rounded-full p-2 text-slate-muted hover:bg-white/5 hover:text-slate-soft"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="overflow-x-auto p-6">
                <table className="w-full min-w-[600px] text-left">
                  <thead>
                    <tr className="border-b border-white/5">
                      <th className="pb-6 pt-2 font-medium text-slate-muted">Feature</th>
                      {selectedData.map(offer => (
                        <th key={offer.id} className="pb-6 pt-2 text-center">
                          <div className="flex flex-col items-center gap-2">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-primary/20 text-indigo-primary">
                              <Building2 className="h-5 w-5" />
                            </div>
                            <span className="text-sm font-bold text-slate-soft">Offer {offer.id.slice(0, 6)}</span>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {[
                      { label: "Interest Rate", key: "interest_rate" as keyof OfferResponse, suffix: "%", type: 'min' as const },
                      { label: "Offered Amount", key: "offered_amount" as keyof OfferResponse, prefix: "₹", type: 'max' as const },
                      { label: "Tenure", key: "tenure_months" as keyof OfferResponse, suffix: " Months", type: 'max' as const },
                      { label: "Monthly EMI", key: "emi_amount" as keyof OfferResponse, prefix: "₹", type: 'min' as const },
                    ].map((row) => {
                      const bestVal = getBestValue(row.key, row.type);
                      return (
                        <tr key={row.key} className="group">
                          <td className="py-6 text-sm font-medium text-slate-muted">{row.label}</td>
                          {selectedData.map(offer => {
                            const val = offer[row.key] as number;
                            const isBest = val === bestVal;
                            return (
                              <td key={offer.id} className="py-6 text-center">
                                <span className={cn(
                                  "inline-block rounded-full px-3 py-1 text-lg font-bold",
                                  isBest ? "bg-indigo-primary/10 text-indigo-primary" : "text-slate-soft"
                                )}>
                                  {row.prefix}{row.key === 'offered_amount' || row.key === 'emi_amount'
                                    ? Number(val).toLocaleString()
                                    : val}{row.suffix}
                                </span>
                                {isBest && (
                                  <p className="mt-1 text-[10px] font-bold text-indigo-primary uppercase tracking-widest">Best</p>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                    <tr>
                      <td className="py-8 text-sm font-medium text-slate-muted">Action</td>
                      {selectedData.map(offer => (
                        <td key={offer.id} className="py-8 text-center">
                          <Button
                            size="sm"
                            onClick={() => {
                              setShowComparison(false);
                              handleAcceptOffer(offer.id);
                            }}
                            disabled={offer.status !== "pending" || acceptingId !== null || !!acceptedId}
                          >
                            {offer.status === "accepted" ? "Accepted ✓" : "Select Offer"}
                          </Button>
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Selection Bar */}
      <AnimatePresence>
        {selectedOffers.length > 0 && !showComparison && (
          <motion.div
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            exit={{ y: 100 }}
            className="fixed bottom-8 left-1/2 z-50 flex -translate-x-1/2 items-center gap-6 rounded-full border border-white/10 bg-navy-deep/80 px-8 py-4 shadow-2xl backdrop-blur-xl"
          >
            <div className="flex items-center gap-4">
              <div className="flex -space-x-3">
                {selectedData.map(offer => (
                  <div
                    key={offer.id}
                    className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-navy-deep bg-indigo-primary/30 text-indigo-primary"
                  >
                    <Building2 className="h-4 w-4" />
                  </div>
                ))}
              </div>
              <p className="text-sm font-medium text-slate-soft">
                {selectedOffers.length} {selectedOffers.length === 1 ? 'offer' : 'offers'} selected
              </p>
            </div>
            <div className="h-6 w-px bg-white/10" />
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setSelectedOffers([])}
                className="text-sm font-medium text-slate-muted hover:text-slate-soft"
              >
                Clear
              </button>
              <Button 
                size="sm" 
                disabled={selectedOffers.length < 2}
                onClick={() => setShowComparison(true)}
              >
                Compare Now
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
