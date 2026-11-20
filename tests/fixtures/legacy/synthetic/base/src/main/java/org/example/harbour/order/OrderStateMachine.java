package org.example.harbour.order;

import java.time.LocalDateTime;
import java.util.Enumeration;
import java.util.Hashtable;
import java.util.Vector;
import java.util.logging.Logger;

import org.example.harbour.model.Order;
import org.example.harbour.model.OrderStatus;

/**
 * Moves orders from one status to the next and keeps a small in-memory
 * history per order id for the support screen.
 */
public class OrderStateMachine {

    private static final Logger LOG = Logger.getLogger(OrderStateMachine.class.getName());

    /** order id (Long) to Vector of history lines (String). */
    private final Hashtable history = new Hashtable();

    /**
     * Tells whether an order may go from one status to another.
     */
    public boolean isTransitionAllowed(OrderStatus from, OrderStatus to) {
        if (from == null || to == null) {
            return false;
        }
        if (from == OrderStatus.NEW && to == OrderStatus.CONFIRMED) {
            return true;
        }
        if (from == OrderStatus.CONFIRMED && to == OrderStatus.PICKED) {
            return true;
        }
        if (from == OrderStatus.PICKED && to == OrderStatus.SHIPPED) {
            return true;
        }
        if (from == OrderStatus.SHIPPED && to == OrderStatus.DELIVERED) {
            return true;
        }
        if (to == OrderStatus.CANCELLED) {
            if (from == OrderStatus.NEW || from == OrderStatus.CONFIRMED || from == OrderStatus.PICKED) {
                return true;
            }
            return false;
        }
        return false;
    }

    /**
     * Changes the status of the order or throws when the change is not allowed.
     */
    public void apply(Order order, OrderStatus target) {
        OrderStatus current = order.getStatus();
        if (!isTransitionAllowed(current, target)) {
            throw new OrderException("order " + order.getId() + " cannot go from " + current + " to " + target,
                    "BAD_TRANSITION");
        }
        order.setStatus(target);
        note(order.getId(), current + " -> " + target);
        LOG.info("order " + order.getId() + ": " + current + " -> " + target);
    }

    private void note(long orderId, String text) {
        Long key = new Long(orderId);
        Vector lines = (Vector) history.get(key);
        if (lines == null) {
            lines = new Vector();
            history.put(key, lines);
        }
        lines.addElement(LocalDateTime.now() + " " + text);
    }

    /**
     * Returns the history of one order as plain text, one line per change.
     */
    public String describe(long orderId) {
        Vector lines = (Vector) history.get(new Long(orderId));
        if (lines == null) {
            return "";
        }
        StringBuffer sb = new StringBuffer();
        Enumeration e = lines.elements();
        while (e.hasMoreElements()) {
            sb.append((String) e.nextElement());
            sb.append('\n');
        }
        return sb.toString();
    }

    /**
     * Forgets the history of orders that are done. Called by the nightly job.
     */
    public int purgeFinished(Vector finishedIds) {
        int removed = 0;
        for (int i = 0; i < finishedIds.size(); i++) {
            if (history.remove(finishedIds.elementAt(i)) != null) {
                removed++;
            }
        }
        return removed;
    }
}
