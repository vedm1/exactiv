package org.example.harbour.invoice;

/**
 * Invoice problems: bad state change, storage failure, missing data.
 */
public class InvoiceException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public InvoiceException(String message) {
        super(message);
    }

    public InvoiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
