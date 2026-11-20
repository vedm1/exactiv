package org.example.harbour.customer;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import org.example.harbour.model.Customer;
import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;

/**
 * Sums the paid net amounts of one customer over a time window.
 */
public class TurnoverCalculator {

    public BigDecimal last12Months(Customer customer, List<Invoice> invoices, LocalDate today) {
        LocalDate from = today.minusMonths(12);
        return invoices.stream()
                .filter(i -> i.getCustomerId() == customer.getId())
                .filter(i -> i.getStatus() == InvoiceStatus.PAID)
                .filter(i -> i.getIssueDate() != null && !i.getIssueDate().isBefore(from)
                        && !i.getIssueDate().isAfter(today))
                .map(Invoice::getNet)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    /**
     * Largest single invoice of the customer in the list, or zero.
     */
    public BigDecimal largestInvoice(Customer customer, List<Invoice> invoices) {
        BigDecimal best = BigDecimal.ZERO;
        for (Invoice inv : invoices) {
            if (inv.getCustomerId() == customer.getId() && inv.getNet().compareTo(best) > 0) {
                best = inv.getNet();
            }
        }
        return best;
    }
}
