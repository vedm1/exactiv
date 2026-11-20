package org.example.harbour.tax;

/**
 * Raised when no tax can be determined for a line.
 */
public class TaxException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public TaxException(String message) {
        super(message);
    }
}
