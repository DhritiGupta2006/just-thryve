/**
 * loanService – thin facade over loansApi / offersApi that exposes
 * the canonical loan-lifecycle operations used by UI components.
 */

import { loansApi, offersApi, LoanApplyPayload, LoanResponse, OfferResponse } from './api';

export const loanService = {
  /** Create a new loan application (borrower only). */
  applyLoan(data: LoanApplyPayload): Promise<{ loan_id: string; status: string }> {
    return loansApi.apply(data);
  },

  /** List loans visible to the current user. */
  getLoans(params?: { status?: string; limit?: number; offset?: number }): Promise<LoanResponse[]> {
    return loansApi.list(params);
  },

  /** Fetch a single loan by ID. */
  getLoan(loanId: string): Promise<LoanResponse> {
    return loansApi.get(loanId);
  },

  /** Submit a loan for ML underwriting. */
  submitLoan(loanId: string): Promise<Record<string, unknown>> {
    return loansApi.submit(loanId);
  },

  /**
   * Get all offers for a loan via the nested route
   * GET /loans/{loanId}/offers.
   */
  getOffers(loanId: string): Promise<OfferResponse[]> {
    return loansApi.getOffers(loanId);
  },

  /**
   * Accept a specific offer via the RESTful PATCH route
   * PATCH /loans/{loanId}/offers/{offerId}/accept.
   */
  acceptOffer(loanId: string, offerId: string): Promise<Record<string, unknown>> {
    return loansApi.patchAcceptOffer(loanId, offerId);
  },
};
