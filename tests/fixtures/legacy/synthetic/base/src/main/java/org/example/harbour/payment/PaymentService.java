package org.example.harbour.payment;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.Hashtable;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.example.harbour.model.Customer;
import org.example.harbour.model.Invoice;
import org.example.harbour.model.Payment;

/**
 * Entry point for the payment screens and the nightly statement job.
 */
public class PaymentService {

    private static final Logger LOG = Logger.getLogger(PaymentService.class.getName());

    private final PaymentDao dao = new PaymentDao();
    private final PaymentAllocator allocator = new PaymentAllocator();
    private final BankStatementImporter importer = new BankStatementImporter();

    /**
     * Books a payment of a customer and spreads it over the open invoices.
     * The caller owns the transaction.
     */
    public List<Allocation> bookPayment(Connection con, Customer customer, BigDecimal amount, LocalDate paidOn,
            List<Invoice> invoices) throws SQLException {
        List<Invoice> open = allocator.openInvoicesOf(customer, invoices);
        List<Allocation> allocations = allocator.allocate(customer, amount, open);
        for (Allocation a : allocations) {
            Payment p = new Payment();
            p.setInvoiceNumber(a.getInvoiceNumber());
            p.setAmount(a.getAmount());
            p.setPaidOn(paidOn);
            dao.insert(con, p);
        }
        allocator.applyToInvoices(allocations, invoices);
        return allocations;
    }

    /**
     * Stores the payments found by a statement import.
     */
    public int storeImported(Connection con, ImportResult result) {
        int stored = 0;
        for (Payment p : result.getMatched()) {
            try {
                dao.insert(con, p);
                stored++;
            } catch (SQLException e) {
                LOG.log(Level.WARNING, "could not store imported payment for " + p.getInvoiceNumber(), e);
                result.getSuspense().add("DB-ERROR;" + p.getInvoiceNumber() + ";" + p.getAmount());
            }
        }
        return stored;
    }

    public Hashtable<String, BigDecimal> paidByInvoice(Connection con, List<Invoice> invoices) throws SQLException {
        Hashtable<String, BigDecimal> table = new Hashtable<String, BigDecimal>();
        for (Invoice inv : invoices) {
            table.put(inv.getNumber(), dao.paidAmount(con, inv.getNumber()));
        }
        return table;
    }

    public long cancelPayment(Connection con, long paymentId, LocalDate today) throws SQLException {
        return dao.reverse(con, paymentId, today);
    }

    public BankStatementImporter getImporter() {
        return importer;
    }
}
