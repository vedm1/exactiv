package org.example.harbour.payment;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.logging.Logger;

import org.example.harbour.model.Customer;
import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;

/**
 * Spreads an incoming payment over the open invoices of a customer.
 */
public class PaymentAllocator {

    private static final Logger LOG = Logger.getLogger(PaymentAllocator.class.getName());

    /**
     * Picks the invoices that can still receive money.
     */
    public List<Invoice> openInvoicesOf(Customer customer, List<Invoice> all) {
        List<Invoice> open = new ArrayList<Invoice>();
        for (Invoice inv : all) {
            if (inv.getCustomerId() != customer.getId()) {
                continue;
            }
            if (inv.getStatus() == InvoiceStatus.ISSUED || inv.getStatus() == InvoiceStatus.OVERDUE) {
                open.add(inv);
            }
        }
        return open;
    }

    public List<Allocation> allocate(Customer customer, BigDecimal amount, List<Invoice> openInvoices) {
        List<Invoice> sorted = new ArrayList<Invoice>(openInvoices);
        sorted.sort(Comparator.comparing(Invoice::getIssueDate));
        List<Allocation> result = new ArrayList<Allocation>();
        BigDecimal remaining = amount;
        for (Invoice inv : sorted) {
            if (remaining.signum() <= 0) {
                break;
            }
            BigDecimal due = inv.getTotal();
            BigDecimal part = remaining.min(due);
            result.add(new Allocation(inv.getNumber(), part, part.compareTo(due) == 0));
            remaining = remaining.subtract(part);
        }
        if (remaining.signum() > 0) {
            customer.setCreditBalance(customer.getCreditBalance().add(remaining));
            LOG.info("overpayment of " + remaining + " kept as credit for customer " + customer.getId());
        }
        return result;
    }

    /**
     * Marks the invoices that were settled by the allocation as paid.
     */
    public void applyToInvoices(List<Allocation> allocations, List<Invoice> invoices) {
        for (Allocation a : allocations) {
            if (!a.isSettled()) {
                continue;
            }
            for (Invoice inv : invoices) {
                if (a.getInvoiceNumber().equals(inv.getNumber())) {
                    inv.setStatus(InvoiceStatus.PAID);
                }
            }
        }
    }
}
