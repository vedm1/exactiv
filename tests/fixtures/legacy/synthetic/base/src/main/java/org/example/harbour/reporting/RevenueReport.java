package org.example.harbour.reporting;

import java.math.BigDecimal;
import java.time.YearMonth;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.logging.Logger;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;

/**
 * Revenue figures for the management report.
 */
public class RevenueReport {

    private static final Logger LOG = Logger.getLogger(RevenueReport.class.getName());

    public Map<YearMonth, BigDecimal> monthlyNet(List<Invoice> invoices) {
        Map<YearMonth, BigDecimal> result = new TreeMap<YearMonth, BigDecimal>();
        for (Invoice inv : invoices) {
            if (inv.getStatus() == InvoiceStatus.DRAFT || inv.getStatus() == InvoiceStatus.CANCELLED) {
                continue;
            }
            if (inv.getIssueDate() == null) {
                LOG.warning("invoice without issue date skipped: " + inv.getNumber());
                continue;
            }
            YearMonth month = YearMonth.from(inv.getIssueDate());
            BigDecimal sum = result.get(month);
            if (sum == null) {
                sum = BigDecimal.ZERO;
            }
            result.put(month, sum.add(inv.getNet()));
        }
        return result;
    }

    /**
     * Sum of all months of one year in a monthly result.
     */
    public BigDecimal yearTotal(Map<YearMonth, BigDecimal> monthly, int year) {
        BigDecimal total = BigDecimal.ZERO;
        Iterator<Map.Entry<YearMonth, BigDecimal>> it = monthly.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<YearMonth, BigDecimal> e = it.next();
            if (e.getKey().getYear() == year) {
                total = total.add(e.getValue());
            }
        }
        return total;
    }

    /**
     * Average of the months that have a value. Zero for an empty report.
     */
    public BigDecimal monthlyAverage(Map<YearMonth, BigDecimal> monthly) {
        if (monthly.isEmpty()) {
            return BigDecimal.ZERO;
        }
        BigDecimal total = BigDecimal.ZERO;
        for (BigDecimal v : monthly.values()) {
            total = total.add(v);
        }
        return total.divide(new BigDecimal(monthly.size()), 2, java.math.RoundingMode.HALF_EVEN);
    }

    /**
     * Month with the highest value, or null when there is no data.
     */
    public YearMonth bestMonth(Map<YearMonth, BigDecimal> monthly) {
        YearMonth best = null;
        BigDecimal max = null;
        for (Map.Entry<YearMonth, BigDecimal> e : monthly.entrySet()) {
            if (max == null || e.getValue().compareTo(max) > 0) {
                max = e.getValue();
                best = e.getKey();
            }
        }
        return best;
    }
}
