package org.example.harbour.model;

import java.math.BigDecimal;

/**
 * One invoice line.
 */
public class InvoiceLine implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private String sku;
    private String description;
    private int quantity = 1;
    private BigDecimal net = BigDecimal.ZERO;
    private BigDecimal taxRate = BigDecimal.ZERO;

    public String getSku() { return sku; }

    public void setSku(String sku) { this.sku = sku; }

    public String getDescription() { return description; }

    public void setDescription(String description) { this.description = description; }

    public int getQuantity() { return quantity; }

    public void setQuantity(int quantity) { this.quantity = quantity; }

    public BigDecimal getNet() { return net; }

    public void setNet(BigDecimal net) { this.net = net; }

    public BigDecimal getTaxRate() { return taxRate; }

    public void setTaxRate(BigDecimal taxRate) { this.taxRate = taxRate; }

}
