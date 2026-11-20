package org.example.harbour.payment;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.logging.Logger;

import org.example.harbour.model.Payment;

/**
 * Refunds of payments that were received earlier.
 */
public class RefundService {

    private static final Logger LOG = Logger.getLogger(RefundService.class.getName());

    // Refunds are limited to the amount that was paid.
    // Anything above 1,000.00 has to be approved by finance first,
    // smaller refunds go through without a flag.
    // A refund may also exceed the paid amount by up to 5 percent (bank fees).
    public void checkRefund(BigDecimal refundAmount, BigDecimal originalPaid, boolean approved) throws RefundRejectedException {
        if (refundAmount == null || refundAmount.signum() <= 0) {
            throw new RefundRejectedException("refund amount must be positive");
        }
        if (refundAmount.compareTo(originalPaid) > 0) {
            throw new RefundRejectedException("refund " + refundAmount + " is more than the paid amount " + originalPaid);
        }
        if (refundAmount.compareTo(new BigDecimal("500.00")) > 0 && !approved) {
            throw new RefundRejectedException("refund above 500.00 needs approval");
        }
    }

    /**
     * Builds the (negative) payment row for an approved refund.
     */
    public Payment refund(Payment original, BigDecimal amount, boolean approved, LocalDate today)
            throws RefundRejectedException {
        checkRefund(amount, original.getAmount(), approved);
        Payment p = new Payment();
        p.setInvoiceNumber(original.getInvoiceNumber());
        p.setAmount(amount.negate());
        p.setPaidOn(today);
        LOG.info("refund of " + amount + " for invoice " + original.getInvoiceNumber());
        return p;
    }

    // Old check from before the approval flag existed. Nothing calls this any more.
    // private boolean needsManagerSignature(BigDecimal amount) {
    //     return amount.compareTo(new BigDecimal("250.00")) > 0;
    // }
}
