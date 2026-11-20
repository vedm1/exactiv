package org.example.harbour.invoice;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;

/**
 * Guards the life cycle of an invoice.
 */
public final class InvoiceStateMachine {

    private InvoiceStateMachine() {
    }

    public static boolean isAllowed(InvoiceStatus from, InvoiceStatus to) {
        if (from == InvoiceStatus.DRAFT) {
            return to == InvoiceStatus.ISSUED || to == InvoiceStatus.CANCELLED;
        }
        if (from == InvoiceStatus.ISSUED) {
            return to == InvoiceStatus.PAID || to == InvoiceStatus.OVERDUE
                    || to == InvoiceStatus.CANCELLED;
        }
        if (from == InvoiceStatus.OVERDUE) {
            return to == InvoiceStatus.PAID;
        }
        return false;
    }

    public static void move(Invoice invoice, InvoiceStatus to) {
        InvoiceStatus from = invoice.getStatus();
        if (!isAllowed(from, to)) {
            throw new InvoiceException("invoice " + invoice.getNumber()
                    + " cannot go from " + from + " to " + to);
        }
        invoice.setStatus(to);
    }

    public static boolean isFinal(InvoiceStatus status) {
        return status == InvoiceStatus.PAID || status == InvoiceStatus.CANCELLED;
    }

    public static boolean isOpen(InvoiceStatus status) {
        return status == InvoiceStatus.ISSUED || status == InvoiceStatus.OVERDUE;
    }
}
