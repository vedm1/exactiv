package org.example.harbour.invoice;

import java.time.LocalDate;

import org.example.harbour.model.Customer;
import org.example.harbour.util.Dates;

/**
 * Sets the payment due date of an invoice.
 */
public class DueDateCalculator {

    private static final int NEW_CUSTOMER_TERMS_DAYS = 14;
    private static final int NEW_CUSTOMER_WINDOW_DAYS = 90;

    public LocalDate dueDate(Customer customer, LocalDate issueDate) {
        int days = customer.getPaymentTermsDays();
        LocalDate created = customer.getCreatedOn();
        if (created != null && Dates.daysBetween(created, issueDate) < NEW_CUSTOMER_WINDOW_DAYS) {
            days = NEW_CUSTOMER_TERMS_DAYS;
        }
        return issueDate.plusDays(days);
    }

    public boolean isOverdue(LocalDate dueDate, LocalDate today) {
        return today.isAfter(dueDate);
    }
}
