package org.example.harbour.invoice;

import java.math.BigDecimal;
import java.util.Iterator;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceLine;

/**
 * Plain text rendering of an invoice for the mail body.
 */
public class InvoiceFormatter {

    private static final String EOL = "\r\n";

    public String format(Invoice inv) {
        StringBuffer sb = new StringBuffer();
        sb.append("Invoice ").append(inv.getNumber()).append(EOL);
        sb.append("Date: ").append(inv.getIssueDate()).append(EOL);
        sb.append("Due: ").append(inv.getDueDate()).append(EOL);
        sb.append(EOL);
        Iterator<InvoiceLine> it = inv.getLines().iterator();
        int pos = 1;
        while (it.hasNext()) {
            InvoiceLine l = it.next();
            sb.append(pos++).append(". ").append(l.getSku());
            sb.append(" x ").append(l.getQuantity());
            sb.append("  ").append(l.getNet().toPlainString());
            sb.append(" (").append(percent(l.getTaxRate())).append("%)").append(EOL);
        }
        sb.append(EOL);
        sb.append("Net:   ").append(inv.getNet().toPlainString()).append(EOL);
        sb.append("Tax:   ").append(inv.getTax().toPlainString()).append(EOL);
        sb.append("Total: ").append(inv.getTotal().toPlainString()).append(' ').append(inv.getCurrency());
        sb.append(EOL);
        if (inv.getLateFee().signum() > 0) {
            sb.append("Late fee: ").append(inv.getLateFee().toPlainString()).append(EOL);
        }
        return sb.toString();
    }

    private String percent(BigDecimal rate) {
        return rate.multiply(new BigDecimal("100")).stripTrailingZeros().toPlainString();
    }

    public String subject(Invoice inv) {
        return "Your invoice " + inv.getNumber();
    }
}
