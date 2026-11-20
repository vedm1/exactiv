package org.example.harbour.order;

import org.example.harbour.model.Order;
import org.example.harbour.model.OrderStatus;

/**
 * Callback for code that wants to know when an order changes status.
 */
public interface OrderListener {

    void statusChanged(Order order, OrderStatus from, OrderStatus to);
}
