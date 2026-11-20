package org.example.harbour.inventory;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

/**
 * JDBC access to the stock and reservation tables. The caller owns the
 * connection and the transaction.
 */
public class StockDao {

    private static final Logger LOG = Logger.getLogger(StockDao.class.getName());

    private static final int MAX_VERSION_RETRIES = 3;

    /**
     * Reads the free quantity and version of a sku. Unknown skus have no stock.
     */
    public StockLevel findLevel(Connection con, String sku) throws SQLException {
        PreparedStatement ps = con.prepareStatement("SELECT quantity, version FROM stock WHERE sku = ?");
        try {
            ps.setString(1, sku);
            ResultSet rs = ps.executeQuery();
            try {
                if (rs.next()) {
                    return new StockLevel(sku, rs.getInt(1), rs.getLong(2));
                }
                return new StockLevel(sku, 0, 0L);
            } finally {
                rs.close();
            }
        } finally {
            ps.close();
        }
    }

    /**
     * Adds delta (negative to take stock) to the free quantity of a sku.
     */
    public void updateStockWithRetry(Connection con, String sku, int delta) throws SQLException {
        for (int attempt = 0; attempt <= MAX_VERSION_RETRIES; attempt++) {
            StockLevel level = findLevel(con, sku);
            int newQuantity = level.getQuantity() + delta;
            if (newQuantity < 0) {
                throw new InsufficientStockException(sku, -newQuantity);
            }
            PreparedStatement ps = con.prepareStatement(
                    "UPDATE stock SET quantity = ?, version = version + 1 WHERE sku = ? AND version = ?");
            int rows;
            try {
                ps.setInt(1, newQuantity);
                ps.setString(2, sku);
                ps.setLong(3, level.getVersion());
                rows = ps.executeUpdate();
            } finally {
                ps.close();
            }
            if (rows == 1) {
                return;
            }
            LOG.fine("version conflict on " + sku + ", attempt " + (attempt + 1));
        }
        throw new StockConflictException("stock of " + sku + " is changing too fast, giving up");
    }

    public long insertReservation(Connection con, Reservation r) throws SQLException {
        PreparedStatement ps = con.prepareStatement(
                "INSERT INTO reservation (order_id, sku, quantity, reserved_at, prepayment, paid, released) "
                + "VALUES (?,?,?,?,?,?,0)", Statement.RETURN_GENERATED_KEYS);
        try {
            ps.setLong(1, r.getOrderId());
            ps.setString(2, r.getSku());
            ps.setInt(3, r.getQuantity());
            ps.setTimestamp(4, Timestamp.valueOf(r.getReservedAt()));
            ps.setBoolean(5, r.isPrepayment());
            ps.setBoolean(6, r.isPaid());
            ps.executeUpdate();
            ResultSet keys = ps.getGeneratedKeys();
            try {
                return keys.next() ? keys.getLong(1) : 0L;
            } finally {
                keys.close();
            }
        } finally {
            ps.close();
        }
    }

    /**
     * Reservations that are still held, optionally only those of one order (orderId greater than 0).
     */
    public List<Reservation> findOpenReservations(Connection con, long orderId) throws SQLException {
        String sql = "SELECT id, order_id, sku, quantity, reserved_at, prepayment, paid FROM reservation "
                + "WHERE released = 0" + (orderId > 0 ? " AND order_id = ?" : "");
        List<Reservation> result = new ArrayList<Reservation>();
        PreparedStatement ps = con.prepareStatement(sql);
        try {
            if (orderId > 0) {
                ps.setLong(1, orderId);
            }
            ResultSet rs = ps.executeQuery();
            while (rs.next()) {
                Reservation r = new Reservation();
                r.setId(rs.getLong(1));
                r.setOrderId(rs.getLong(2));
                r.setSku(rs.getString(3));
                r.setQuantity(rs.getInt(4));
                r.setReservedAt(rs.getTimestamp(5).toLocalDateTime());
                r.setPrepayment(rs.getBoolean(6));
                r.setPaid(rs.getBoolean(7));
                result.add(r);
            }
            rs.close();
        } finally {
            ps.close();
        }
        return result;
    }

    public void markReleased(Connection con, long reservationId) throws SQLException {
        PreparedStatement ps = con.prepareStatement("UPDATE reservation SET released = 1 WHERE id = ?");
        try {
            ps.setLong(1, reservationId);
            ps.executeUpdate();
        } finally {
            ps.close();
        }
    }
}
