package org.example.harbour.payment;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

import org.example.harbour.model.Payment;

/**
 * JDBC access to the payment table. The table is append-only for the application.
 */
public class PaymentDao {

    private static final Logger LOG = Logger.getLogger(PaymentDao.class.getName());

    private static final String SELECT =
            "SELECT id, invoice_number, amount, paid_on, reversal_of FROM payment ";

    public Payment findById(Connection con, long id) throws SQLException {
        PreparedStatement ps = con.prepareStatement(SELECT + "WHERE id = ?");
        ResultSet rs = null;
        try {
            ps.setLong(1, id);
            rs = ps.executeQuery();
            return rs.next() ? map(rs) : null;
        } finally {
            closeQuietly(rs, ps);
        }
    }

    public List<Payment> findByInvoice(Connection con, String invoiceNumber) throws SQLException {
        List<Payment> out = new ArrayList<Payment>();
        PreparedStatement ps = con.prepareStatement(SELECT + "WHERE invoice_number = ? ORDER BY id");
        ResultSet rs = null;
        try {
            ps.setString(1, invoiceNumber);
            rs = ps.executeQuery();
            while (rs.next()) {
                out.add(map(rs));
            }
        } finally {
            closeQuietly(rs, ps);
        }
        return out;
    }

    public long insert(Connection con, Payment p) throws SQLException {
        PreparedStatement ps = con.prepareStatement(
                "INSERT INTO payment (invoice_number, amount, paid_on, reversal_of) VALUES (?, ?, ?, ?)",
                Statement.RETURN_GENERATED_KEYS);
        ResultSet keys = null;
        try {
            ps.setString(1, p.getInvoiceNumber());
            ps.setBigDecimal(2, p.getAmount());
            ps.setDate(3, Date.valueOf(p.getPaidOn()));
            if (p.getReversalOf() == null) {
                ps.setNull(4, java.sql.Types.BIGINT);
            } else {
                ps.setLong(4, p.getReversalOf().longValue());
            }
            ps.executeUpdate();
            keys = ps.getGeneratedKeys();
            keys.next();
            return keys.getLong(1);
        } finally {
            closeQuietly(keys, ps);
        }
    }

    public long reverse(Connection con, long paymentId, LocalDate on) throws SQLException {
        Payment original = findById(con, paymentId);
        if (original == null) {
            throw new SQLException("no payment with id " + paymentId);
        }
        if (original.getReversalOf() != null) {
            throw new SQLException("payment " + paymentId + " is itself a reversal");
        }
        Payment reversal = new Payment();
        reversal.setInvoiceNumber(original.getInvoiceNumber());
        reversal.setAmount(original.getAmount().negate());
        reversal.setPaidOn(on);
        reversal.setReversalOf(Long.valueOf(paymentId));
        long id = insert(con, reversal);
        LOG.info("payment " + paymentId + " reversed by row " + id);
        return id;
    }

    /**
     * Net paid amount of an invoice: payments plus reversals and refunds.
     */
    public BigDecimal paidAmount(Connection con, String invoiceNumber) throws SQLException {
        BigDecimal sum = BigDecimal.ZERO;
        for (Payment p : findByInvoice(con, invoiceNumber)) {
            sum = sum.add(p.getAmount());
        }
        return sum;
    }

    // TODO: archive rows older than 10 years into payment_archive
    // con.createStatement().executeUpdate("INSERT INTO payment_archive SELECT * FROM payment WHERE paid_on < ...");

    private Payment map(ResultSet rs) throws SQLException {
        Payment p = new Payment();
        p.setId(rs.getLong("id"));
        p.setInvoiceNumber(rs.getString("invoice_number"));
        p.setAmount(rs.getBigDecimal("amount"));
        p.setPaidOn(rs.getDate("paid_on").toLocalDate());
        long rev = rs.getLong("reversal_of");
        if (!rs.wasNull()) {
            p.setReversalOf(Long.valueOf(rev));
        }
        return p;
    }

    private static void closeQuietly(ResultSet rs, Statement st) {
        try {
            if (rs != null) {
                rs.close();
            }
            if (st != null) {
                st.close();
            }
        } catch (SQLException e) {
            LOG.fine("close failed: " + e.getMessage());
        }
    }
}
