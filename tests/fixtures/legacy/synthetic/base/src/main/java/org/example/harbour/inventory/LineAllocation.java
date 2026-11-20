package org.example.harbour.inventory;

/**
 * One part of an order line after stock allocation. A line is either one
 * part (all in stock or all on backorder) or two parts.
 */
public class LineAllocation {

    private final String sku;
    private final int quantity;
    private final boolean backorder;

    public LineAllocation(String sku, int quantity, boolean backorder) {
        this.sku = sku;
        this.quantity = quantity;
        this.backorder = backorder;
    }

    public String getSku() {
        return sku;
    }

    public int getQuantity() {
        return quantity;
    }

    public boolean isBackorder() {
        return backorder;
    }

    @Override
    public String toString() {
        return sku + " x" + quantity + (backorder ? " (backorder)" : "");
    }
}
