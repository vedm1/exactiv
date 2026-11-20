package org.example.harbour.invoice;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import javax.sql.DataSource;

/**
 * Search queries for the back office screen. Returns light rows, not full invoices.
 */
public class InvoiceSearchDao {

    private final DataSource dataSource;

    public InvoiceSearchDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    public static class Row {
        public String number;
        public long customerId;
        public String status;
        public LocalDate issueDate;
        public String total;
    }

    public List<Row> byDateRange(LocalDate from, LocalDate to, String statusOrNull) {
        StringBuilder sql = new StringBuilder(
                "SELECT number, customer_id, status, issue_date, total FROM invoice "
                + "WHERE issue_date >= ? AND issue_date <= ?");
        if (statusOrNull != null) {
            sql.append(" AND status = ?");
        }
        sql.append(" ORDER BY issue_date, number");
        List<Row> rows = new ArrayList<Row>();
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql.toString())) {
            ps.setDate(1, Date.valueOf(from));
            ps.setDate(2, Date.valueOf(to));
            if (statusOrNull != null) {
                ps.setString(3, statusOrNull);
            }
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Row r = new Row();
                    r.number = rs.getString(1);
                    r.customerId = rs.getLong(2);
                    r.status = rs.getString(3);
                    r.issueDate = rs.getDate(4).toLocalDate();
                    r.total = rs.getBigDecimal(5).toPlainString();
                    rows.add(r);
                }
            }
        } catch (SQLException e) {
            throw new InvoiceException("invoice search failed", e);
        }
        return rows;
    }

    public int countByCustomer(long customerId) {
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement("SELECT COUNT(*) FROM invoice WHERE customer_id = ?")) {
            ps.setLong(1, customerId);
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                return rs.getInt(1);
            }
        } catch (SQLException e) {
            throw new InvoiceException("invoice count failed", e);
        }
    }

    public String findNumberByOrder(long orderId) {
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement("SELECT number FROM invoice WHERE order_id = ?")) {
            ps.setLong(1, orderId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getString(1) : null;
            }
        } catch (SQLException e) {
            throw new InvoiceException("invoice lookup failed", e);
        }
    }
}
