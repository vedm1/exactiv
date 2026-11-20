package org.example.harbour.inventory;

/**
 * Not enough stock and the product cannot be put on backorder.
 */
public class InsufficientStockException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private final String sku;
    private final int missing;

    public InsufficientStockException(String sku, int missing) {
        super("not enough stock for " + sku + ", missing " + missing);
        this.sku = sku;
        this.missing = missing;
    }

    public String getSku() {
        return sku;
    }

    public int getMissing() {
        return missing;
    }
}
