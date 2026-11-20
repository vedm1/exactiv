package org.example.harbour.invoice;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;

/**
 * Read-only roll-up of a customer's invoices for the account screen.
 */
public class InvoiceSummary {

    private final int openCount;
    private final int overdueCount;
    private final BigDecimal openTotal;
    private final LocalDate oldestDue;

    public InvoiceSummary(List<Invoice> invoices) {
        List<Invoice> open = invoices.stream()
                .filter(i -> InvoiceStateMachine.isOpen(i.getStatus()))
                .collect(Collectors.toList());
        this.openCount = open.size();
        this.overdueCount = (int) open.stream()
                .filter(i -> i.getStatus() == InvoiceStatus.OVERDUE)
                .count();
        this.openTotal = open.stream()
                .map(Invoice::getTotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        this.oldestDue = open.stream()
                .map(Invoice::getDueDate)
                .min(LocalDate::compareTo)
                .orElse(null);
    }

    public int getOpenCount() {
        return openCount;
    }

    public int getOverdueCount() {
        return overdueCount;
    }

    public BigDecimal getOpenTotal() {
        return openTotal;
    }

    public LocalDate getOldestDue() {
        return oldestDue;
    }

    public boolean hasOverdue() {
        return overdueCount > 0;
    }

    @Override
    public String toString() {
        return openCount + " open, " + overdueCount + " overdue, total " + openTotal;
    }
}
