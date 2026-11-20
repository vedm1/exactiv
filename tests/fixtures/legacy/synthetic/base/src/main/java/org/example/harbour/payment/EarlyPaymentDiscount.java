package org.example.harbour.payment;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;

import org.example.harbour.model.Invoice;
import org.example.harbour.util.Dates;

/**
 * Cash discount ("Skonto") for invoices that are paid quickly.
 */
public class EarlyPaymentDiscount {

    private static final BigDecimal EARLY_RATE = new BigDecimal("0.02");

    public BigDecimal discountFor(Invoice invoice, LocalDate paidOn) {
        if (invoice.getIssueDate() == null || paidOn == null) {
            return BigDecimal.ZERO;
        }
        long days = Dates.daysBetween(invoice.getIssueDate(), paidOn);
        boolean hasLateFee = invoice.getLateFee() != null && invoice.getLateFee().signum() != 0;
        if (days <= 10 && !hasLateFee && !invoice.isDisputed()) {
            return invoice.getTotal().multiply(EARLY_RATE).setScale(2, RoundingMode.HALF_EVEN);
        }
        return BigDecimal.ZERO;
    }

    /**
     * Amount the customer has to pay when the discount is taken.
     */
    public BigDecimal amountToPay(Invoice invoice, LocalDate paidOn) {
        return invoice.getTotal().subtract(discountFor(invoice, paidOn));
    }
}
