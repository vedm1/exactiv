package org.example.harbour.security;

import java.math.BigDecimal;
import java.util.logging.Logger;

import org.example.harbour.model.Customer;
import org.example.harbour.model.User;

/**
 * Changing a credit limit: role check first, then the approval rule.
 */
public class CreditLimitApproval {

    private static final Logger LOG = Logger.getLogger(CreditLimitApproval.class.getName());

    private static final BigDecimal FOUR_EYES_ABOVE = new BigDecimal("50000");

    private final AccessPolicy policy;

    public CreditLimitApproval(AccessPolicy policy) {
        this.policy = policy;
    }

    public void checkApproval(BigDecimal newLimit, User requester, User approver) {
        if (newLimit.compareTo(FOUR_EYES_ABOVE) <= 0) {
            return;
        }
        if (approver == null) {
            throw new AccessDeniedException("limit " + newLimit + " needs a second approver");
        }
        if (approver.getName() != null && approver.getName().equals(requester.getName())) {
            throw new AccessDeniedException("approver must not be the requester");
        }
    }

    public void changeLimit(Customer customer, BigDecimal newLimit, User requester, User approver) {
        policy.requireCreditLimitRight(requester);
        if (newLimit.signum() < 0) {
            throw new IllegalArgumentException("credit limit cannot be negative");
        }
        checkApproval(newLimit, requester, approver);
        BigDecimal old = customer.getCreditLimit();
        customer.setCreditLimit(newLimit);
        LOG.info("credit limit of customer " + customer.getId() + " changed from " + old + " to " + newLimit);
    }
}
