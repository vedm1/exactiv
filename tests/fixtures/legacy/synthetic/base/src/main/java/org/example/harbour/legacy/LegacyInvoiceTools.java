package org.example.harbour.legacy;

import java.math.BigDecimal;
import java.util.Enumeration;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.Vector;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;

/**
 * Static helpers that the old batch jobs still call. Written before generics were used here.
 * Do not add new callers.
 */
public class LegacyInvoiceTools {

    private static final String SEP = ";";

    private static Hashtable statusNames = new Hashtable();

    static {
        statusNames.put(InvoiceStatus.DRAFT, "D");
        statusNames.put(InvoiceStatus.ISSUED, "I");
        statusNames.put(InvoiceStatus.PAID, "P");
        statusNames.put(InvoiceStatus.OVERDUE, "O");
        statusNames.put(InvoiceStatus.CANCELLED, "C");
    }

    /**
     * One line per invoice for the nightly flat file.
     */
    public static String toFlatLine(Invoice inv) {
        StringBuffer sb = new StringBuffer();
        sb.append(inv.getNumber()).append(SEP);
        sb.append(inv.getCustomerId()).append(SEP);
        sb.append(statusCode(inv.getStatus())).append(SEP);
        sb.append(inv.getIssueDate()).append(SEP);
        sb.append(inv.getDueDate()).append(SEP);
        sb.append(inv.getNet()).append(SEP);
        sb.append(inv.getTax()).append(SEP);
        sb.append(inv.getTotal());
        return sb.toString();
    }

    public static String statusCode(InvoiceStatus status) {
        Object code = statusNames.get(status);
        if (code == null) {
            return "?";
        }
        return (String) code;
    }

    public static Vector toFlatLines(Vector invoices) {
        Vector out = new Vector();
        Iterator it = invoices.iterator();
        while (it.hasNext()) {
            Invoice inv = (Invoice) it.next();
            out.addElement(toFlatLine(inv));
        }
        return out;
    }

    /**
     * Counts invoices per status code.
     */
    public static Hashtable countByStatus(Vector invoices) {
        Hashtable counts = new Hashtable();
        for (int i = 0; i < invoices.size(); i++) {
            Invoice inv = (Invoice) invoices.elementAt(i);
            String code = statusCode(inv.getStatus());
            Integer old = (Integer) counts.get(code);
            if (old == null) {
                counts.put(code, new Integer(1));
            } else {
                counts.put(code, new Integer(old.intValue() + 1));
            }
        }
        return counts;
    }

    public static String describeCounts(Hashtable counts) {
        StringBuffer sb = new StringBuffer();
        Enumeration keys = counts.keys();
        while (keys.hasMoreElements()) {
            Object key = keys.nextElement();
            if (sb.length() > 0) {
                sb.append(", ");
            }
            sb.append(key).append('=').append(counts.get(key));
        }
        return sb.toString();
    }

    public static BigDecimal totalOf(Vector invoices) {
        BigDecimal sum = new BigDecimal("0.00");
        for (int i = 0; i < invoices.size(); i++) {
            Invoice inv = (Invoice) invoices.get(i);
            if (inv.getTotal() != null) {
                sum = sum.add(inv.getTotal());
            }
        }
        return sum;
    }

    public static String padNumber(long n, int width) {
        StringBuffer sb = new StringBuffer(String.valueOf(n));
        while (sb.length() < width) {
            sb.insert(0, '0');
        }
        return sb.toString();
    }

    public static boolean isBlank(String s) {
        return s == null || "".equals(s.trim());
    }

    // TODO replace with String.join once the batch jobs run on the new runtime
    public static String join(Vector parts, String sep) {
        StringBuffer sb = new StringBuffer();
        for (int i = 0; i < parts.size(); i++) {
            if (i > 0) {
                sb.append(sep);
            }
            sb.append(parts.elementAt(i));
        }
        return sb.toString();
    }
}
