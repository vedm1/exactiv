package org.example.harbour.security;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;
import org.example.harbour.model.Role;
import org.example.harbour.model.User;

/**
 * Role checks used by the screens and the services.
 */
public class AccessPolicy {

    public boolean mayCancelInvoice(User user, Invoice invoice) {
        if (invoice.getStatus() != InvoiceStatus.ISSUED) {
            return true;
        }
        if (user == null || user.getRoles() == null) {
            return false;
        }
        return user.getRoles().contains(Role.ROLE_FINANCE);
    }

    public boolean mayChangeCreditLimit(User user) {
        if (user == null || user.getRoles() == null) {
            return false;
        }
        return user.getRoles().contains(Role.ROLE_ADMIN);
    }

    public void requireCancelRight(User user, Invoice invoice) {
        if (!mayCancelInvoice(user, invoice)) {
            throw new AccessDeniedException("invoice " + invoice.getNumber() + " may not be cancelled by "
                    + (user == null ? "nobody" : user.getName()));
        }
    }

    public void requireCreditLimitRight(User user) {
        if (!mayChangeCreditLimit(user)) {
            throw new AccessDeniedException("credit limits may not be changed by "
                    + (user == null ? "nobody" : user.getName()));
        }
    }

    public boolean hasAny(User user, Role... wanted) {
        if (user == null) {
            return false;
        }
        for (Role r : wanted) {
            if (user.getRoles().contains(r)) {
                return true;
            }
        }
        return false;
    }
}
