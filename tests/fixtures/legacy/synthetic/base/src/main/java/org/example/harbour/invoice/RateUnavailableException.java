package org.example.harbour.invoice;

/**
 * No usable exchange rate exists for the requested day.
 */
public class RateUnavailableException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public RateUnavailableException(String message) {
        super(message);
    }
}
