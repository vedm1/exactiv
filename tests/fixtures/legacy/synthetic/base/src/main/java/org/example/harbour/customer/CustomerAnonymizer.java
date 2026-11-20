package org.example.harbour.customer;

import java.sql.SQLException;
import java.time.LocalDate;
import java.util.Iterator;
import java.util.List;
import java.util.Vector;
import java.util.logging.Logger;

import org.example.harbour.model.Customer;

/**
 * Removes personal data of customers that have been inactive for long enough.
 */
public class CustomerAnonymizer {

    private static final Logger LOG = Logger.getLogger(CustomerAnonymizer.class.getName());

    private static final int RETENTION_YEARS = 10;

    private final CustomerDao dao;

    public CustomerAnonymizer(CustomerDao dao) {
        this.dao = dao;
    }

    /**
     * Tells whether the data of a customer must be anonymised.
     *
     * @param lastInvoiceDate date of the newest invoice of the customer, null if none
     */
    public boolean isDueForAnonymisation(LocalDate lastInvoiceDate, LocalDate today) {
        if (lastInvoiceDate == null) {
            return false;
        }
        LocalDate earliest = lastInvoiceDate.plusYears(RETENTION_YEARS);
        return !today.isBefore(earliest);
    }

    /**
     * Overwrites the personal fields. The id stays, so old invoices still point somewhere.
     */
    public void anonymise(Customer c) {
        c.setName("anonymised-" + c.getId());
        c.setEmail("anonymised-" + c.getId() + "@invalid.example");
        c.setVatId(null);
        c.setIban(null);
    }

    /**
     * Runs the job for a list of customers. Returns the ids that were changed.
     */
    public List<Long> run(List<Customer> customers, java.util.Map<Long, LocalDate> lastInvoice, LocalDate today) {
        Vector<Long> done = new Vector<Long>();
        Iterator<Customer> it = customers.iterator();
        while (it.hasNext()) {
            Customer c = it.next();
            LocalDate last = lastInvoice.get(Long.valueOf(c.getId()));
            if (isDueForAnonymisation(last, today)) {
                anonymise(c);
                try {
                    dao.update(c);
                    done.add(Long.valueOf(c.getId()));
                } catch (SQLException e) {
                    LOG.warning("could not save anonymised customer " + c.getId() + ": " + e.getMessage());
                }
            }
        }
        return done;
    }
}
