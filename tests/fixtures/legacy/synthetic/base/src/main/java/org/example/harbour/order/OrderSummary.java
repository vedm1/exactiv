package org.example.harbour.order;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

import org.example.harbour.model.Order;
import org.example.harbour.model.OrderStatus;

/**
 * Flat view of an order for list screens and the REST layer.
 */
public class OrderSummary implements Serializable {

    private static final long serialVersionUID = 1L;

    private long orderId;
    private long customerId;
    private OrderStatus status;
    private BigDecimal total;
    private String currency;
    private int lineCount;
    private LocalDateTime createdAt;
    private boolean approvalPending;

    public static OrderSummary of(Order order) {
        OrderSummary s = new OrderSummary();
        s.orderId = order.getId();
        s.customerId = order.getCustomerId();
        s.status = order.getStatus();
        s.total = order.getTotal();
        s.currency = order.getCurrency();
        s.lineCount = order.getLines() == null ? 0 : order.getLines().size();
        s.createdAt = order.getCreatedAt();
        return s;
    }

    public long getOrderId() {
        return orderId;
    }

    public long getCustomerId() {
        return customerId;
    }

    public OrderStatus getStatus() {
        return status;
    }

    public BigDecimal getTotal() {
        return total;
    }

    public String getCurrency() {
        return currency;
    }

    public int getLineCount() {
        return lineCount;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public boolean isApprovalPending() {
        return approvalPending;
    }

    public void setApprovalPending(boolean approvalPending) {
        this.approvalPending = approvalPending;
    }

    @Override
    public String toString() {
        return "OrderSummary[" + orderId + ", " + status + ", " + total + " " + currency + "]";
    }
}
