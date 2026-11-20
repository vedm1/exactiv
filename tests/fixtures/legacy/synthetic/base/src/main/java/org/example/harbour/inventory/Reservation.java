package org.example.harbour.inventory;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * Stock held for a confirmed order.
 */
public class Reservation implements Serializable {

    private static final long serialVersionUID = 1L;

    private long id;
    private long orderId;
    private String sku;
    private int quantity;
    private LocalDateTime reservedAt;
    private boolean prepayment;
    private boolean paid;
    private boolean released;

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public long getOrderId() {
        return orderId;
    }

    public void setOrderId(long orderId) {
        this.orderId = orderId;
    }

    public String getSku() {
        return sku;
    }

    public void setSku(String sku) {
        this.sku = sku;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    public LocalDateTime getReservedAt() {
        return reservedAt;
    }

    public void setReservedAt(LocalDateTime reservedAt) {
        this.reservedAt = reservedAt;
    }

    public boolean isPrepayment() {
        return prepayment;
    }

    public void setPrepayment(boolean prepayment) {
        this.prepayment = prepayment;
    }

    public boolean isPaid() {
        return paid;
    }

    public void setPaid(boolean paid) {
        this.paid = paid;
    }

    public boolean isReleased() {
        return released;
    }

    public void setReleased(boolean released) {
        this.released = released;
    }
}
