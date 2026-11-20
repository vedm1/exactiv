package org.example.harbour.audit;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.Map;
import java.util.TreeMap;

/**
 * A named list of unit prices by SKU.
 */
public class PriceList {

    private final long id;
    private final String name;
    private final Map<String, BigDecimal> prices = new TreeMap<String, BigDecimal>();

    public PriceList(long id, String name) {
        this.id = id;
        this.name = name;
    }

    public long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public BigDecimal priceOf(String sku) {
        return prices.get(sku);
    }

    /**
     * Raw setter. Services that change prices on behalf of a user go through PriceListService.
     */
    void put(String sku, BigDecimal price) {
        prices.put(sku, price);
    }

    public Map<String, BigDecimal> asMap() {
        return Collections.unmodifiableMap(prices);
    }

    public int size() {
        return prices.size();
    }
}
