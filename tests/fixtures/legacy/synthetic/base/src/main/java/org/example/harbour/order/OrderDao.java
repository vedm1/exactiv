package org.example.harbour.order;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.sql.DataSource;

import org.example.harbour.model.Address;
import org.example.harbour.model.Carrier;
import org.example.harbour.model.Order;
import org.example.harbour.model.OrderLine;
import org.example.harbour.model.OrderStatus;

/**
 * Plain JDBC access to the order tables. One connection per call, no pooling
 * logic here, the data source does that.
 */
public class OrderDao {

    private static final Logger LOG = Logger.getLogger(OrderDao.class.getName());

    private static final String INSERT_ORDER =
            "INSERT INTO orders (customer_id, status, currency, total, prepayment, carrier, created_at, "
            + "ship_street, ship_city, ship_postal, ship_country) VALUES (?,?,?,?,?,?,?,?,?,?,?)";

    private static final String INSERT_LINE =
            "INSERT INTO order_lines (order_id, line_no, sku, quantity, unit_price, discount) VALUES (?,?,?,?,?,?)";

    private static final String SELECT_ORDER =
            "SELECT id, customer_id, status, currency, total, prepayment, carrier, created_at, confirmed_at, "
            + "ship_street, ship_city, ship_postal, ship_country FROM orders WHERE id = ?";

    private final DataSource dataSource;

    public OrderDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * Inserts the order and its lines in one transaction and sets the new id on the order.
     */
    public long insert(Order order) {
        Connection con = null;
        PreparedStatement ps = null;
        try {
            con = dataSource.getConnection();
            con.setAutoCommit(false);
            ps = con.prepareStatement(INSERT_ORDER, Statement.RETURN_GENERATED_KEYS);
            ps.setLong(1, order.getCustomerId());
            ps.setString(2, order.getStatus().name());
            ps.setString(3, order.getCurrency());
            ps.setBigDecimal(4, order.getTotal());
            ps.setBoolean(5, order.isPrepayment());
            ps.setString(6, order.getCarrier().name());
            ps.setTimestamp(7, Timestamp.valueOf(order.getCreatedAt()));
            Address to = order.getShipping();
            ps.setString(8, to.getStreet());
            ps.setString(9, to.getCity());
            ps.setString(10, to.getPostalCode());
            ps.setString(11, to.getCountryCode());
            ps.executeUpdate();
            ResultSet keys = ps.getGeneratedKeys();
            if (keys.next()) {
                order.setId(keys.getLong(1));
            }
            keys.close();
            insertLines(con, order);
            con.commit();
            return order.getId();
        } catch (Exception e) {
            rollbackQuietly(con);
            LOG.log(Level.SEVERE, "insert of order failed", e);
            throw new OrderException("order could not be saved", e);
        } finally {
            closeQuietly(ps);
            closeQuietly(con);
        }
    }

    private void insertLines(Connection con, Order order) throws SQLException {
        PreparedStatement ps = con.prepareStatement(INSERT_LINE);
        try {
            int no = 1;
            for (OrderLine line : order.getLines()) {
                ps.setLong(1, order.getId());
                ps.setInt(2, no++);
                ps.setString(3, line.getSku());
                ps.setInt(4, line.getQuantity());
                ps.setBigDecimal(5, line.getUnitPrice());
                ps.setBigDecimal(6, line.getDiscount());
                ps.addBatch();
            }
            ps.executeBatch();
        } finally {
            ps.close();
        }
    }

    /**
     * Loads an order with its lines, or returns null when the id is unknown.
     */
    public Order findById(long id) {
        Connection con = null;
        PreparedStatement ps = null;
        ResultSet rs = null;
        try {
            con = dataSource.getConnection();
            ps = con.prepareStatement(SELECT_ORDER);
            ps.setLong(1, id);
            rs = ps.executeQuery();
            if (!rs.next()) {
                return null;
            }
            Order order = map(rs);
            order.setLines(loadLines(con, id));
            return order;
        } catch (SQLException e) {
            throw new OrderException("order " + id + " could not be read", e);
        } finally {
            closeQuietly(rs);
            closeQuietly(ps);
            closeQuietly(con);
        }
    }

    private Order map(ResultSet rs) throws SQLException {
        Order o = new Order();
        o.setId(rs.getLong("id"));
        o.setCustomerId(rs.getLong("customer_id"));
        o.setStatus(OrderStatus.valueOf(rs.getString("status")));
        o.setCurrency(rs.getString("currency"));
        o.setTotal(rs.getBigDecimal("total"));
        o.setPrepayment(rs.getBoolean("prepayment"));
        o.setCarrier(Carrier.valueOf(rs.getString("carrier")));
        Timestamp created = rs.getTimestamp("created_at");
        if (created != null) {
            o.setCreatedAt(created.toLocalDateTime());
        }
        Timestamp confirmed = rs.getTimestamp("confirmed_at");
        if (confirmed != null) {
            o.setConfirmedAt(confirmed.toLocalDateTime());
        }
        Address a = new Address();
        a.setStreet(rs.getString("ship_street"));
        a.setCity(rs.getString("ship_city"));
        a.setPostalCode(rs.getString("ship_postal"));
        a.setCountryCode(rs.getString("ship_country"));
        o.setShipping(a);
        return o;
    }

    private List<OrderLine> loadLines(Connection con, long orderId) throws SQLException {
        List<OrderLine> lines = new ArrayList<OrderLine>();
        PreparedStatement ps = con.prepareStatement(
                "SELECT sku, quantity, unit_price, discount FROM order_lines WHERE order_id = ? ORDER BY line_no");
        try {
            ps.setLong(1, orderId);
            ResultSet rs = ps.executeQuery();
            while (rs.next()) {
                OrderLine l = new OrderLine();
                l.setSku(rs.getString(1));
                l.setQuantity(rs.getInt(2));
                l.setUnitPrice(rs.getBigDecimal(3));
                BigDecimal d = rs.getBigDecimal(4);
                l.setDiscount(d == null ? BigDecimal.ZERO : d);
                lines.add(l);
            }
            rs.close();
        } finally {
            ps.close();
        }
        return lines;
    }

    /**
     * Writes the new status and, when set, the confirmation time.
     */
    public void updateStatus(Order order) {
        String sql = "UPDATE orders SET status = ?, confirmed_at = ? WHERE id = ?";
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setString(1, order.getStatus().name());
            if (order.getConfirmedAt() == null) {
                ps.setNull(2, java.sql.Types.TIMESTAMP);
            } else {
                ps.setTimestamp(2, Timestamp.valueOf(order.getConfirmedAt()));
            }
            ps.setLong(3, order.getId());
            int rows = ps.executeUpdate();
            if (rows != 1) {
                throw new OrderException("order " + order.getId() + " not found for update");
            }
        } catch (SQLException e) {
            throw new OrderException("status update failed for order " + order.getId(), e);
        }
    }

    /**
     * All order ids of a customer, newest first.
     */
    public List<Long> findIdsByCustomer(long customerId) {
        List<Long> ids = new ArrayList<Long>();
        String sql = "SELECT id FROM orders WHERE customer_id = ? ORDER BY created_at DESC";
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setLong(1, customerId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    ids.add(Long.valueOf(rs.getLong(1)));
                }
            }
        } catch (SQLException e) {
            throw new OrderException("could not list orders of customer " + customerId, e);
        }
        return ids;
    }

    private static void rollbackQuietly(Connection con) {
        if (con != null) {
            try {
                con.rollback();
            } catch (SQLException ignore) {
                // the original error is more important
            }
        }
    }

    private static void closeQuietly(AutoCloseable c) {
        if (c != null) {
            try {
                c.close();
            } catch (Exception ignore) {
                // nothing sensible to do
            }
        }
    }
}
