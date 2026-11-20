package org.example.harbour.payment;

import java.math.BigDecimal;

/**
 * One part of a payment that was assigned to an invoice.
 */
public class Allocation {

    private final String invoiceNumber;
    private final BigDecimal amount;
    private final boolean settled;

    public Allocation(String invoiceNumber, BigDecimal amount, boolean settled) {
        this.invoiceNumber = invoiceNumber;
        this.amount = amount;
        this.settled = settled;
    }

    public String getInvoiceNumber() {
        return invoiceNumber;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    /**
     * True when the invoice is fully covered by this part.
     */
    public boolean isSettled() {
        return settled;
    }

    @Override
    public String toString() {
        return invoiceNumber + ":" + amount.toPlainString() + (settled ? " (settled)" : " (partial)");
    }
}
