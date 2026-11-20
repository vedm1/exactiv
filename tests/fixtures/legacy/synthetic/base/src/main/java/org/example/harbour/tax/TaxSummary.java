package org.example.harbour.tax;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Groups line taxes by rate for the footer of an invoice.
 */
public class TaxSummary {

    private final Map<BigDecimal, BigDecimal> byRate = new LinkedHashMap<BigDecimal, BigDecimal>();

    public TaxSummary(List<TaxResult> results) {
        for (TaxResult r : results) {
            BigDecimal old = byRate.get(r.getRate());
            byRate.put(r.getRate(), old == null ? r.getAmount() : old.add(r.getAmount()));
        }
    }

    public Map<BigDecimal, BigDecimal> getByRate() {
        return byRate;
    }

    public BigDecimal total() {
        BigDecimal t = BigDecimal.ZERO;
        for (BigDecimal v : byRate.values()) {
            t = t.add(v);
        }
        return t;
    }

    public String render() {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<BigDecimal, BigDecimal> e : byRate.entrySet()) {
            sb.append(e.getKey().movePointRight(2).stripTrailingZeros().toPlainString());
            sb.append("%: ").append(e.getValue().toPlainString()).append('\n');
        }
        return sb.toString();
    }
}
