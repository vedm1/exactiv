package org.example.harbour.invoice;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.sql.DataSource;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceLine;
import org.example.harbour.model.InvoiceStatus;

/**
 * JDBC access to invoice and invoice_line.
 */
public class InvoiceDao {

    private static final Logger LOG = Logger.getLogger(InvoiceDao.class.getName());

    private final DataSource dataSource;

    public InvoiceDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    public long insert(Invoice inv) {
        Connection con = null;
        try {
            con = dataSource.getConnection();
            con.setAutoCommit(false);
            PreparedStatement ps = con.prepareStatement(
                    "INSERT INTO invoice (number, customer_id, order_id, status, issue_date, due_date, "
                    + "net, tax, total, late_fee, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, inv.getNumber());
            ps.setLong(2, inv.getCustomerId());
            ps.setLong(3, inv.getOrderId());
            ps.setString(4, inv.getStatus().name());
            ps.setDate(5, Date.valueOf(inv.getIssueDate()));
            ps.setDate(6, Date.valueOf(inv.getDueDate()));
            ps.setBigDecimal(7, inv.getNet());
            ps.setBigDecimal(8, inv.getTax());
            ps.setBigDecimal(9, inv.getTotal());
            ps.setBigDecimal(10, inv.getLateFee());
            ps.setString(11, inv.getCurrency());
            ps.executeUpdate();
            ResultSet keys = ps.getGeneratedKeys();
            keys.next();
            long id = keys.getLong(1);
            insertLines(con, id, inv.getLines());
            con.commit();
            inv.setId(id);
            return id;
        } catch (Exception e) {
            rollbackQuietly(con);
            LOG.log(Level.SEVERE, "invoice insert failed", e);
            throw new InvoiceException("invoice insert failed", e);
        } finally {
            closeQuietly(con);
        }
    }

    private void insertLines(Connection con, long invoiceId, List<InvoiceLine> lines) throws SQLException {
        PreparedStatement ps = con.prepareStatement(
                "INSERT INTO invoice_line (invoice_id, line_no, sku, description, quantity, net, tax_rate) "
                + "VALUES (?,?,?,?,?,?,?)");
        int no = 1;
        for (InvoiceLine l : lines) {
            ps.setLong(1, invoiceId);
            ps.setInt(2, no++);
            ps.setString(3, l.getSku());
            ps.setString(4, l.getDescription());
            ps.setInt(5, l.getQuantity());
            ps.setBigDecimal(6, l.getNet());
            ps.setBigDecimal(7, l.getTaxRate());
            ps.addBatch();
        }
        ps.executeBatch();
        ps.close();
    }

    public void updateStatus(long invoiceId, InvoiceStatus status) {
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement("UPDATE invoice SET status = ? WHERE id = ?")) {
            ps.setString(1, status.name());
            ps.setLong(2, invoiceId);
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new InvoiceException("status update failed", e);
        }
    }

    public List<Invoice> findOpenByCustomer(long customerId) {
        List<Invoice> result = new ArrayList<Invoice>();
        String sql = "SELECT id, number, status, issue_date, due_date, net, tax, total, late_fee, currency "
                + "FROM invoice WHERE customer_id = ? AND status IN ('ISSUED','OVERDUE') ORDER BY due_date";
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setLong(1, customerId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    result.add(map(rs, customerId));
                }
            }
        } catch (SQLException e) {
            throw new InvoiceException("open invoice query failed", e);
        }
        return result;
    }

    private Invoice map(ResultSet rs, long customerId) throws SQLException {
        Invoice inv = new Invoice();
        inv.setId(rs.getLong("id"));
        inv.setNumber(rs.getString("number"));
        inv.setCustomerId(customerId);
        inv.setStatus(InvoiceStatus.valueOf(rs.getString("status")));
        inv.setIssueDate(rs.getDate("issue_date").toLocalDate());
        inv.setDueDate(rs.getDate("due_date").toLocalDate());
        inv.setNet(rs.getBigDecimal("net"));
        inv.setTax(rs.getBigDecimal("tax"));
        inv.setTotal(rs.getBigDecimal("total"));
        inv.setLateFee(rs.getBigDecimal("late_fee"));
        inv.setCurrency(rs.getString("currency"));
        return inv;
    }

    public boolean numberExists(String number) {
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement("SELECT 1 FROM invoice WHERE number = ?")) {
            ps.setString(1, number);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        } catch (SQLException e) {
            throw new InvoiceException("number check failed", e);
        }
    }

    /**
     * Next free sequence value for a year. Reads the highest used and adds one.
     */
    public long nextSequence(int year) {
        String prefix = "INV-" + year + "-";
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(
                        "SELECT MAX(number) FROM invoice WHERE number LIKE ?")) {
            ps.setString(1, prefix + "%");
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                String max = rs.getString(1);
                if (max == null) {
                    return 1L;
                }
                return Long.parseLong(max.substring(prefix.length())) + 1L;
            }
        } catch (SQLException e) {
            throw new InvoiceException("sequence lookup failed", e);
        }
    }

    public BigDecimal sumOpenTotal(long customerId) {
        BigDecimal sum = BigDecimal.ZERO;
        for (Invoice i : findOpenByCustomer(customerId)) {
            sum = sum.add(i.getTotal());
        }
        return sum;
    }

    private void rollbackQuietly(Connection con) {
        if (con != null) {
            try {
                con.rollback();
            } catch (SQLException ignore) {
                // nothing more to do
            }
        }
    }

    private void closeQuietly(Connection con) {
        if (con != null) {
            try {
                con.close();
            } catch (SQLException ignore) {
                // nothing more to do
            }
        }
    }
}
