package org.example.harbour.reporting;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;
import org.example.harbour.util.Dates;

/**
 * Open receivables grouped by how long they are past due. Only for reading by the finance team.
 */
public class AgingReport {

    public static final String NOT_DUE = "not due";
    public static final String BUCKET_1 = "1-30";
    public static final String BUCKET_2 = "31-60";
    public static final String BUCKET_3 = "over 60";

    public Map<String, BigDecimal> build(List<Invoice> invoices, LocalDate today) {
        Map<String, BigDecimal> buckets = new LinkedHashMap<String, BigDecimal>();
        buckets.put(NOT_DUE, BigDecimal.ZERO);
        buckets.put(BUCKET_1, BigDecimal.ZERO);
        buckets.put(BUCKET_2, BigDecimal.ZERO);
        buckets.put(BUCKET_3, BigDecimal.ZERO);
        for (Invoice inv : invoices) {
            if (inv.getStatus() != InvoiceStatus.ISSUED && inv.getStatus() != InvoiceStatus.OVERDUE) {
                continue;
            }
            String key = bucketOf(inv, today);
            buckets.put(key, buckets.get(key).add(inv.getTotal()));
        }
        return buckets;
    }

    String bucketOf(Invoice inv, LocalDate today) {
        if (inv.getDueDate() == null) {
            return NOT_DUE;
        }
        long late = Dates.daysBetween(inv.getDueDate(), today);
        if (late <= 0) {
            return NOT_DUE;
        } else if (late <= 30) {
            return BUCKET_1;
        } else if (late <= 60) {
            return BUCKET_2;
        }
        return BUCKET_3;
    }

    public BigDecimal totalOpen(Map<String, BigDecimal> buckets) {
        BigDecimal sum = BigDecimal.ZERO;
        for (BigDecimal b : buckets.values()) {
            sum = sum.add(b);
        }
        return sum;
    }
}
