package org.example.harbour.order;

import java.math.BigDecimal;
import java.util.Iterator;
import java.util.List;

import org.example.harbour.model.Order;
import org.example.harbour.model.OrderLine;

/**
 * Static helpers that add up order lines. Old code, kept as it is because
 * the reports call it from several places.
 */
public final class OrderTotals {

    private OrderTotals() {
    }

    /**
     * Gross amount of one line before any discount.
     */
    public static BigDecimal lineGross(OrderLine line) {
        if (line.getUnitPrice() == null) {
            return BigDecimal.ZERO;
        }
        return line.getUnitPrice().multiply(new BigDecimal(line.getQuantity()));
    }

    /**
     * Sum of all lines, discounts taken off.
     */
    public static BigDecimal sum(Order order) {
        BigDecimal total = BigDecimal.ZERO;
        List lines = order.getLines();
        Iterator it = lines.iterator();
        while (it.hasNext()) {
            OrderLine line = (OrderLine) it.next();
            BigDecimal amount = lineGross(line);
            if (line.getDiscount() != null) {
                amount = amount.subtract(line.getDiscount());
            }
            total = total.add(amount);
        }
        return total;
    }

    /**
     * Number of items over all lines.
     */
    public static int itemCount(Order order) {
        int n = 0;
        for (OrderLine line : order.getLines()) {
            n += line.getQuantity();
        }
        return n;
    }

    // public static BigDecimal averageLine(Order order) {
    //     return sum(order).divide(new BigDecimal(order.getLines().size()));
    // }
}
