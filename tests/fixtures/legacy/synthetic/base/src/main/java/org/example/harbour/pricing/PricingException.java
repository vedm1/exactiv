package org.example.harbour.pricing;

/**
 * Thrown when a price cannot be worked out.
 */
public class PricingException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public PricingException(String message) {
        super(message);
    }

    public PricingException(String message, Throwable cause) {
        super(message, cause);
    }
}
