package org.example.harbour.customer;

import java.math.BigDecimal;
import java.sql.SQLException;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.example.harbour.model.Customer;
import org.example.harbour.model.CustomerState;
import org.example.harbour.model.CustomerTier;
import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceStatus;
import org.example.harbour.util.Dates;
import org.example.harbour.util.Strings;

/**
 * Customer master data: registration, tier and state changes.
 */
public class CustomerService {

    private static final Logger LOG = Logger.getLogger(CustomerService.class.getName());

    private final CustomerDao dao;
    private final TurnoverCalculator turnover = new TurnoverCalculator();

    public CustomerService(CustomerDao dao) {
        this.dao = dao;
    }

    /**
     * Creates a new customer record. The e-mail address goes through assignEmail
     * so that it is stored in the normal form.
     */
    public Customer register(String name, String email, String countryCode, String vatId, LocalDate today)
            throws SQLException {
        if (Strings.isEmpty(name)) {
            throw new IllegalArgumentException("name is required");
        }
        Customer c = new Customer();
        c.setName(name.trim());
        c.setCountryCode(countryCode == null ? "DE" : countryCode.toUpperCase());
        if (!Strings.isEmpty(vatId)) {
            if (!VatIdValidator.isValidVatId(vatId)) {
                throw new IllegalArgumentException("VAT id not valid: " + vatId);
            }
            c.setVatId(vatId.trim().toUpperCase());
        }
        c.setCreatedOn(today);
        assignEmail(c, email);
        long id = dao.insert(c);
        c.setId(id);
        LOG.info("customer registered, id " + id);
        return c;
    }

    /**
     * Stores an e-mail address on the customer.
     */
    public void assignEmail(Customer customer, String rawEmail) throws SQLException {
        if (rawEmail == null) {
            throw new IllegalArgumentException("e-mail is required");
        }
        String normalized = rawEmail.trim().toLowerCase();
        if (normalized.length() == 0 || normalized.indexOf('@') < 1) {
            throw new IllegalArgumentException("e-mail not usable: " + rawEmail);
        }
        if (dao.emailTaken(normalized, customer.getId())) {
            throw new DuplicateEmailException(normalized);
        }
        customer.setEmail(normalized);
    }

    /**
     * Works out the tier a customer should have today.
     */
    public CustomerTier evaluateTier(Customer customer, BigDecimal turnoverLast12Months, LocalDate today) {
        CustomerTier current = customer.getTier();
        long months = ChronoUnit.MONTHS.between(customer.getCreatedOn(), today);
        if (current != CustomerTier.GOLD && months >= 12
                && turnoverLast12Months.compareTo(new BigDecimal("20000")) >= 0) {
            return CustomerTier.GOLD;
        }
        if (current == CustomerTier.GOLD
                && turnoverLast12Months.compareTo(new BigDecimal("10000")) < 0) {
            return CustomerTier.SILVER;
        }
        return current;
    }

    /**
     * Works out whether the customer is active or blocked, given the customer's invoices.
     */
    public CustomerState nextState(Customer customer, List<Invoice> invoices, LocalDate today) {
        boolean anyOverdue = false;
        boolean overdueTooLong = false;
        for (Invoice inv : invoices) {
            if (inv.getCustomerId() != customer.getId()) {
                continue;
            }
            if (inv.getStatus() == InvoiceStatus.OVERDUE) {
                anyOverdue = true;
                if (inv.getDueDate() != null && Dates.daysBetween(inv.getDueDate(), today) > 60) {
                    overdueTooLong = true;
                }
            }
        }
        if (customer.getState() == CustomerState.ACTIVE && overdueTooLong) {
            return CustomerState.BLOCKED;
        }
        if (customer.getState() == CustomerState.BLOCKED && !anyOverdue) {
            return CustomerState.ACTIVE;
        }
        return customer.getState();
    }

    /**
     * Nightly job body: re-evaluates tier and state of one customer and saves the result.
     */
    public boolean refresh(Customer customer, List<Invoice> invoices, LocalDate today) {
        boolean changed = false;
        try {
            BigDecimal t = turnover.last12Months(customer, invoices, today);
            CustomerTier tier = evaluateTier(customer, t, today);
            if (tier != customer.getTier()) {
                LOG.info("tier of customer " + customer.getId() + ": " + customer.getTier() + " -> " + tier);
                customer.setTier(tier);
                changed = true;
            }
            CustomerState state = nextState(customer, invoices, today);
            if (state != customer.getState()) {
                LOG.info("state of customer " + customer.getId() + ": " + customer.getState() + " -> " + state);
                customer.setState(state);
                changed = true;
            }
            if (changed) {
                dao.update(customer);
            }
        } catch (Exception e) {
            LOG.log(Level.SEVERE, "refresh failed for customer " + customer.getId(), e);
        }
        return changed;
    }

    public Customer find(long id) throws SQLException {
        return dao.findById(id);
    }

    // TODO: merge duplicate customers (ticket was closed, never done)
    // public void merge(Customer keep, Customer drop) { ... }
}
