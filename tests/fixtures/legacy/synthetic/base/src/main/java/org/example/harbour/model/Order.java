package org.example.harbour.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * A customer order.
 */
public class Order implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private long id;
    private long customerId;
    private List<OrderLine> lines = new ArrayList<OrderLine>();
    private OrderStatus status = OrderStatus.NEW;
    private LocalDateTime createdAt;
    private LocalDateTime confirmedAt;
    private Address shipping;
    private String currency = "EUR";
    private BigDecimal total = BigDecimal.ZERO;
    private boolean prepayment = false;
    private Carrier carrier = Carrier.GROUND;

    public long getId() { return id; }

    public void setId(long id) { this.id = id; }

    public long getCustomerId() { return customerId; }

    public void setCustomerId(long customerId) { this.customerId = customerId; }

    public List<OrderLine> getLines() { return lines; }

    public void setLines(List<OrderLine> lines) { this.lines = lines; }

    public OrderStatus getStatus() { return status; }

    public void setStatus(OrderStatus status) { this.status = status; }

    public LocalDateTime getCreatedAt() { return createdAt; }

    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getConfirmedAt() { return confirmedAt; }

    public void setConfirmedAt(LocalDateTime confirmedAt) { this.confirmedAt = confirmedAt; }

    public Address getShipping() { return shipping; }

    public void setShipping(Address shipping) { this.shipping = shipping; }

    public String getCurrency() { return currency; }

    public void setCurrency(String currency) { this.currency = currency; }

    public BigDecimal getTotal() { return total; }

    public void setTotal(BigDecimal total) { this.total = total; }

    public boolean isPrepayment() { return prepayment; }

    public void setPrepayment(boolean prepayment) { this.prepayment = prepayment; }

    public Carrier getCarrier() { return carrier; }

    public void setCarrier(Carrier carrier) { this.carrier = carrier; }

}
