package org.example.harbour.shipping;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.sql.DataSource;

/**
 * Notices the carrier did not accept. Support staff work through this table by hand.
 */
public class ParkedNoticeStore {

    private static final Logger LOG = Logger.getLogger(ParkedNoticeStore.class.getName());

    private final DataSource dataSource;

    public ParkedNoticeStore(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * Saves a notice for manual handling. Never throws: a notice that cannot be
     * parked is written to the log so that it is not lost.
     */
    public void park(ShipmentNotice notice, String lastError) {
        String sql = "INSERT INTO parked_notice (order_id, body, last_error, parked_at) VALUES (?,?,?,CURRENT_TIMESTAMP)";
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setLong(1, notice.getOrderId());
            ps.setString(2, notice.toJson());
            ps.setString(3, lastError);
            ps.executeUpdate();
        } catch (SQLException e) {
            LOG.log(Level.SEVERE, "could not park notice, body follows: " + notice.toJson(), e);
        }
    }

    /**
     * Order ids that wait for manual handling.
     */
    public List<Long> waitingOrderIds() {
        List<Long> ids = new ArrayList<Long>();
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement("SELECT order_id FROM parked_notice ORDER BY parked_at");
                ResultSet rs = ps.executeQuery()) {
            while (rs.next()) {
                ids.add(Long.valueOf(rs.getLong(1)));
            }
        } catch (SQLException e) {
            LOG.log(Level.WARNING, "could not read parked notices", e);
        }
        return ids;
    }
}
