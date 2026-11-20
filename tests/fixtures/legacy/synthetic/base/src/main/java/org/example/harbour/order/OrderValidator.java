package org.example.harbour.order;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.example.harbour.model.Address;
import org.example.harbour.model.Order;
import org.example.harbour.model.OrderLine;
import org.example.harbour.util.Strings;

/**
 * Checks an order before it is saved. {@link #check(Order)} collects all
 * problems for the screen, {@link #validateLines(Order)} throws on the first one.
 */
public class OrderValidator {

    private static final Logger LOG = Logger.getLogger(OrderValidator.class.getName());

    private static final Set<String> CURRENCIES = new HashSet<String>(Arrays.asList("EUR", "USD", "GBP", "CHF"));

    /**
     * Collects every problem found in the order. An empty list means the order can be saved.
     */
    public List<String> check(Order order) {
        List<String> problems = new ArrayList<String>();
        if (order == null) {
            problems.add("order is missing");
            return problems;
        }
        if (order.getCustomerId() <= 0) {
            problems.add("customer is missing");
        }
        if (Strings.isEmpty(order.getCurrency()) || !CURRENCIES.contains(order.getCurrency())) {
            problems.add("currency not supported: " + order.getCurrency());
        }
        Address to = order.getShipping();
        if (to == null) {
            problems.add("ship-to address is missing");
        } else {
            if (Strings.isEmpty(to.getCountryCode())) {
                problems.add("ship-to country is missing");
            }
            if (Strings.isEmpty(to.getPostalCode())) {
                problems.add("ship-to postal code is missing");
            }
        }
        try {
            validateLines(order);
        } catch (OrderException e) {
            problems.add(e.getMessage());
        }
        if (LOG.isLoggable(Level.FINE)) {
            LOG.fine("order " + order.getId() + " checked, problems: " + problems.size());
        }
        return problems;
    }

    /**
     * Line count and quantity limits of an order.
     */
    public void validateLines(Order order) {
        List<OrderLine> lines = order.getLines();
        if (lines == null || lines.size() < 1) {
            throw new OrderException("an order needs at least one line", "NO_LINES");
        }
        if (lines.size() > 100) {
            throw new OrderException("an order can have 100 lines at most, got " + lines.size(), "TOO_MANY_LINES");
        }
        for (int i = 0; i < lines.size(); i++) {
            OrderLine line = lines.get(i);
            int qty = line.getQuantity();
            if (qty < 1 || qty > 9999) {
                throw new OrderException("line " + (i + 1) + " has a bad quantity: " + qty, "BAD_QUANTITY");
            }
        }
    }

    /**
     * Quick check used by the batch import: true when no sku appears twice.
     */
    public boolean hasUniqueSkus(Order order) {
        Set<String> seen = new HashSet<String>();
        for (OrderLine line : order.getLines()) {
            if (!seen.add(line.getSku())) {
                return false;
            }
        }
        return true;
    }
}
