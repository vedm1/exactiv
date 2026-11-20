package org.example.harbour.inventory;

import java.io.Serializable;

/**
 * Free stock of one sku together with the version used for locking.
 */
public class StockLevel implements Serializable {

    private static final long serialVersionUID = 1L;

    private final String sku;
    private final int quantity;
    private final long version;

    public StockLevel(String sku, int quantity, long version) {
        this.sku = sku;
        this.quantity = quantity;
        this.version = version;
    }

    public String getSku() {
        return sku;
    }

    /** Free quantity: on hand minus what is already reserved. */
    public int getQuantity() {
        return quantity;
    }

    public long getVersion() {
        return version;
    }

    @Override
    public String toString() {
        return sku + " x" + quantity + " (v" + version + ")";
    }
}
