package org.example.harbour.customer;

/**
 * Raised when an e-mail address is already used by another customer.
 */
public class DuplicateEmailException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private final String email;

    public DuplicateEmailException(String email) {
        super("e-mail already in use: " + email);
        this.email = email;
    }

    public String getEmail() {
        return email;
    }
}
