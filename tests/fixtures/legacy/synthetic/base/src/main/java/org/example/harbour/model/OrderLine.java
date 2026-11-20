package org.example.harbour.model;

import java.math.BigDecimal;

/**
 * One line of an order.
 */
public class OrderLine implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private String sku;
    private int quantity = 1;
    private BigDecimal unitPrice;
    private BigDecimal discount = BigDecimal.ZERO;

    public String getSku() { return sku; }

    public void setSku(String sku) { this.sku = sku; }

    public int getQuantity() { return quantity; }

    public void setQuantity(int quantity) { this.quantity = quantity; }

    public BigDecimal getUnitPrice() { return unitPrice; }

    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }

    public BigDecimal getDiscount() { return discount; }

    public void setDiscount(BigDecimal discount) { this.discount = discount; }

}
