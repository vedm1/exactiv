package org.example.harbour.order;

import java.math.BigDecimal;
import java.util.logging.Logger;

import org.example.harbour.util.Config;

/**
 * Decides whether an order needs a manager before it can be confirmed.
 */
public class OrderApprovalPolicy {

    private static final Logger LOG = Logger.getLogger(OrderApprovalPolicy.class.getName());

    // Orders above 5,000 need manager approval (agreed with sales, see the ticket in the wiki).
    private static final BigDecimal APPROVAL_LIMIT = new BigDecimal("50000");

    /**
     * True when the order total is above the approval limit.
     */
    public boolean needsManagerApproval(BigDecimal orderTotal) {
        BigDecimal limit = APPROVAL_LIMIT;
        String override = Config.get("order.approval.limit", null);
        if (override != null && override.trim().length() > 0) {
            try {
                limit = new BigDecimal(override.trim());
            } catch (NumberFormatException e) {
                LOG.warning("ignoring bad order.approval.limit: " + override);
            }
        }
        return orderTotal.compareTo(limit) > 0;
    }

    /**
     * Text for the confirmation screen.
     */
    public String explain(BigDecimal orderTotal) {
        if (needsManagerApproval(orderTotal)) {
            return "Manager approval needed for " + orderTotal.toPlainString();
        }
        return "No approval needed";
    }
}
