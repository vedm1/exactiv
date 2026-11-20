package org.example.harbour.inventory;

/**
 * The stock row was changed by someone else and the retries ran out.
 */
public class StockConflictException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public StockConflictException(String message) {
        super(message);
    }
}
