package org.example.harbour.shipping;

/**
 * A shipment cannot be planned, priced or announced.
 */
public class ShippingException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public ShippingException(String message) {
        super(message);
    }

    public ShippingException(String message, Throwable cause) {
        super(message, cause);
    }
}
