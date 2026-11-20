package org.example.harbour.model;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * A customer invoice.
 */
public class Invoice implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private long id;
    private String number;
    private long customerId;
    private long orderId;
    private InvoiceStatus status = InvoiceStatus.DRAFT;
    private LocalDate issueDate;
    private LocalDate dueDate;
    private List<InvoiceLine> lines = new ArrayList<InvoiceLine>();
    private BigDecimal net = BigDecimal.ZERO;
    private BigDecimal tax = BigDecimal.ZERO;
    private BigDecimal total = BigDecimal.ZERO;
    private BigDecimal lateFee = BigDecimal.ZERO;
    private String currency = "EUR";
    private boolean disputed = false;

    public long getId() { return id; }

    public void setId(long id) { this.id = id; }

    public String getNumber() { return number; }

    public void setNumber(String number) { this.number = number; }

    public long getCustomerId() { return customerId; }

    public void setCustomerId(long customerId) { this.customerId = customerId; }

    public long getOrderId() { return orderId; }

    public void setOrderId(long orderId) { this.orderId = orderId; }

    public InvoiceStatus getStatus() { return status; }

    public void setStatus(InvoiceStatus status) { this.status = status; }

    public LocalDate getIssueDate() { return issueDate; }

    public void setIssueDate(LocalDate issueDate) { this.issueDate = issueDate; }

    public LocalDate getDueDate() { return dueDate; }

    public void setDueDate(LocalDate dueDate) { this.dueDate = dueDate; }

    public List<InvoiceLine> getLines() { return lines; }

    public void setLines(List<InvoiceLine> lines) { this.lines = lines; }

    public BigDecimal getNet() { return net; }

    public void setNet(BigDecimal net) { this.net = net; }

    public BigDecimal getTax() { return tax; }

    public void setTax(BigDecimal tax) { this.tax = tax; }

    public BigDecimal getTotal() { return total; }

    public void setTotal(BigDecimal total) { this.total = total; }

    public BigDecimal getLateFee() { return lateFee; }

    public void setLateFee(BigDecimal lateFee) { this.lateFee = lateFee; }

    public String getCurrency() { return currency; }

    public void setCurrency(String currency) { this.currency = currency; }

    public boolean isDisputed() { return disputed; }

    public void setDisputed(boolean disputed) { this.disputed = disputed; }

}
