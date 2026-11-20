package org.example.harbour.order;

/**
 * Thrown when an order breaks a constraint or when a state change is refused.
 * The short code is shown in the order screen next to the message.
 */
public class OrderException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private final String code;

    public OrderException(String message) {
        this(message, "ORDER");
    }

    public OrderException(String message, String code) {
        super(message);
        this.code = code;
    }

    public OrderException(String message, Throwable cause) {
        super(message, cause);
        this.code = "ORDER";
    }

    public String getCode() {
        return code;
    }
}
