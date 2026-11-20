package org.example.harbour.payment;

/**
 * A refund request that breaks a payment rule.
 */
public class RefundRejectedException extends Exception {

    private static final long serialVersionUID = 1L;

    public RefundRejectedException(String message) {
        super(message);
    }
}
