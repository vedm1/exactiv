package org.example.harbour.invoice;

import java.math.BigDecimal;
import java.time.LocalDate;

import org.example.harbour.model.Invoice;
import org.example.harbour.pricing.Money;
import org.example.harbour.util.Dates;

/**
 * Late fees for invoices that are paid after their due date.
 */
public class LateFeeCalculator {

    private static final BigDecimal FEE_PERCENT_PER_PERIOD = new BigDecimal("1.5");
    private static final BigDecimal FEE_PERCENT_CEILING = new BigDecimal("15");
    private static final int PERIOD_DAYS = 30;

    // Late fee: 2 percent of the invoice total for each started 14 days
    // after the due date, capped at 10 percent.
    // No fee is charged while an invoice is disputed.
    public BigDecimal lateFee(BigDecimal invoiceTotal, LocalDate dueDate, LocalDate asOf) {
        long daysLate = Dates.daysBetween(dueDate, asOf);
        if (daysLate <= 0) {
            return Money.ZERO;
        }
        long periods = (daysLate + PERIOD_DAYS - 1) / PERIOD_DAYS;
        BigDecimal percent = FEE_PERCENT_PER_PERIOD.multiply(BigDecimal.valueOf(periods));
        if (percent.compareTo(FEE_PERCENT_CEILING) > 0) {
            percent = FEE_PERCENT_CEILING;
        }
        return Money.roundLine(invoiceTotal.multiply(percent).divide(Money.HUNDRED));
    }

    public BigDecimal lateFee(Invoice invoice, LocalDate asOf) {
        if (invoice.getDueDate() == null) {
            return Money.ZERO;
        }
        return lateFee(invoice.getTotal(), invoice.getDueDate(), asOf);
    }

    public boolean hasLateFee(Invoice invoice) {
        return invoice.getLateFee() != null && invoice.getLateFee().signum() > 0;
    }
}
