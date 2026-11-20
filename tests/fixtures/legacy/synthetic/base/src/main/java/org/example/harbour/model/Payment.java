package org.example.harbour.model;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * A payment received.
 */
public class Payment implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private long id;
    private String invoiceNumber;
    private BigDecimal amount;
    private LocalDate paidOn;
    private Long reversalOf;

    public long getId() { return id; }

    public void setId(long id) { this.id = id; }

    public String getInvoiceNumber() { return invoiceNumber; }

    public void setInvoiceNumber(String invoiceNumber) { this.invoiceNumber = invoiceNumber; }

    public BigDecimal getAmount() { return amount; }

    public void setAmount(BigDecimal amount) { this.amount = amount; }

    public LocalDate getPaidOn() { return paidOn; }

    public void setPaidOn(LocalDate paidOn) { this.paidOn = paidOn; }

    public Long getReversalOf() { return reversalOf; }

    public void setReversalOf(Long reversalOf) { this.reversalOf = reversalOf; }

}
