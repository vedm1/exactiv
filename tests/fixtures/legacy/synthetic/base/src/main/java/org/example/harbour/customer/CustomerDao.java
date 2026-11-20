package org.example.harbour.customer;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

import org.example.harbour.model.Customer;
import org.example.harbour.model.CustomerState;
import org.example.harbour.model.CustomerTier;

/**
 * JDBC access to the customer table.
 */
public class CustomerDao {

    private static final String COLUMNS =
            "id, name, email, country_code, vat_id, tier, state, payment_terms_days, "
            + "credit_limit, credit_balance, created_on, partner, group_code, iban";

    private final Connection con;

    public CustomerDao(Connection con) {
        this.con = con;
    }

    public Customer findById(long id) throws SQLException {
        PreparedStatement ps = con.prepareStatement("SELECT " + COLUMNS + " FROM customer WHERE id = ?");
        ResultSet rs = null;
        try {
            ps.setLong(1, id);
            rs = ps.executeQuery();
            if (rs.next()) {
                return map(rs);
            }
            return null;
        } finally {
            close(rs, ps);
        }
    }

    public List<Customer> findByState(CustomerState state) throws SQLException {
        List<Customer> out = new ArrayList<Customer>();
        PreparedStatement ps = con.prepareStatement(
                "SELECT " + COLUMNS + " FROM customer WHERE state = ? ORDER BY id");
        ResultSet rs = null;
        try {
            ps.setString(1, state.name());
            rs = ps.executeQuery();
            while (rs.next()) {
                out.add(map(rs));
            }
        } finally {
            close(rs, ps);
        }
        return out;
    }

    /**
     * True when another customer already uses this (already normalised) address.
     */
    public boolean emailTaken(String normalizedEmail, long exceptCustomerId) throws SQLException {
        PreparedStatement ps = con.prepareStatement(
                "SELECT COUNT(*) FROM customer WHERE email = ? AND id <> ?");
        ResultSet rs = null;
        try {
            ps.setString(1, normalizedEmail);
            ps.setLong(2, exceptCustomerId);
            rs = ps.executeQuery();
            rs.next();
            return rs.getInt(1) > 0;
        } finally {
            close(rs, ps);
        }
    }

    public long insert(Customer c) throws SQLException {
        PreparedStatement ps = con.prepareStatement(
                "INSERT INTO customer (name, email, country_code, vat_id, tier, state, payment_terms_days, "
                + "credit_limit, credit_balance, created_on, partner, group_code, iban) "
                + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                Statement.RETURN_GENERATED_KEYS);
        ResultSet keys = null;
        try {
            bind(ps, c);
            ps.executeUpdate();
            keys = ps.getGeneratedKeys();
            if (keys.next()) {
                return keys.getLong(1);
            }
            throw new SQLException("no generated key for customer");
        } finally {
            close(keys, ps);
        }
    }

    public void update(Customer c) throws SQLException {
        PreparedStatement ps = con.prepareStatement(
                "UPDATE customer SET name = ?, email = ?, country_code = ?, vat_id = ?, tier = ?, state = ?, "
                + "payment_terms_days = ?, credit_limit = ?, credit_balance = ?, created_on = ?, partner = ?, "
                + "group_code = ?, iban = ? WHERE id = ?");
        try {
            bind(ps, c);
            ps.setLong(14, c.getId());
            ps.executeUpdate();
        } finally {
            close(null, ps);
        }
    }

    private void bind(PreparedStatement ps, Customer c) throws SQLException {
        ps.setString(1, c.getName());
        ps.setString(2, c.getEmail());
        ps.setString(3, c.getCountryCode());
        ps.setString(4, c.getVatId());
        ps.setString(5, c.getTier().name());
        ps.setString(6, c.getState().name());
        ps.setInt(7, c.getPaymentTermsDays());
        ps.setBigDecimal(8, c.getCreditLimit());
        ps.setBigDecimal(9, c.getCreditBalance());
        ps.setDate(10, c.getCreatedOn() == null ? null : Date.valueOf(c.getCreatedOn()));
        ps.setBoolean(11, c.isPartner());
        ps.setInt(12, c.getGroupCode());
        ps.setString(13, c.getIban());
    }

    private Customer map(ResultSet rs) throws SQLException {
        Customer c = new Customer();
        c.setId(rs.getLong("id"));
        c.setName(rs.getString("name"));
        c.setEmail(rs.getString("email"));
        c.setCountryCode(rs.getString("country_code"));
        c.setVatId(rs.getString("vat_id"));
        c.setTier(CustomerTier.valueOf(rs.getString("tier")));
        c.setState(CustomerState.valueOf(rs.getString("state")));
        c.setPaymentTermsDays(rs.getInt("payment_terms_days"));
        BigDecimal limit = rs.getBigDecimal("credit_limit");
        c.setCreditLimit(limit == null ? BigDecimal.ZERO : limit);
        BigDecimal bal = rs.getBigDecimal("credit_balance");
        c.setCreditBalance(bal == null ? BigDecimal.ZERO : bal);
        Date created = rs.getDate("created_on");
        if (created != null) {
            c.setCreatedOn(created.toLocalDate());
        }
        c.setPartner(rs.getBoolean("partner"));
        c.setGroupCode(rs.getInt("group_code"));
        c.setIban(rs.getString("iban"));
        return c;
    }

    private static void close(ResultSet rs, Statement st) {
        try {
            if (rs != null) {
                rs.close();
            }
        } catch (SQLException e) {
            // ignore
        }
        try {
            if (st != null) {
                st.close();
            }
        } catch (SQLException e) {
            // ignore
        }
    }
}
