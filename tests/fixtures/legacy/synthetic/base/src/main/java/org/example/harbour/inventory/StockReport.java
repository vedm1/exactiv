package org.example.harbour.inventory;

import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;

/**
 * Small formatting helpers for the stock overview screen.
 */
public final class StockReport {

    private StockReport() {
    }

    /**
     * One line per sku, sorted by sku.
     */
    public static String render(List<StockLevel> levels) {
        StringBuffer sb = new StringBuffer();
        Map<String, StockLevel> sorted = new TreeMap<String, StockLevel>();
        for (StockLevel l : levels) {
            sorted.put(l.getSku(), l);
        }
        for (StockLevel l : sorted.values()) {
            sb.append(l.getSku()).append(';').append(l.getQuantity()).append('\n');
        }
        return sb.toString();
    }

    /**
     * The n skus with the most free stock.
     */
    public static List<String> topSkus(List<StockLevel> levels, int n) {
        return levels.stream()
                .sorted(new Comparator<StockLevel>() {
                    @Override
                    public int compare(StockLevel a, StockLevel b) {
                        return b.getQuantity() - a.getQuantity();
                    }
                })
                .limit(n)
                .map(StockLevel::getSku)
                .collect(Collectors.toList());
    }

    /**
     * Sum of the free quantities over all levels.
     */
    public static long totalUnits(List<StockLevel> levels) {
        long sum = 0;
        for (StockLevel l : levels) {
            sum += l.getQuantity();
        }
        return sum;
    }

    public static List<StockLevel> empty() {
        return Collections.emptyList();
    }
}
