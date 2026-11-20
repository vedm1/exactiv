package org.example.harbour.shipping;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import javax.sql.DataSource;

import org.example.harbour.model.Carrier;

/**
 * JDBC access to the shipment table.
 */
public class ShipmentDao {

    private final DataSource dataSource;

    public ShipmentDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    public void save(ShipmentNotice notice) {
        String sql = "INSERT INTO shipment (order_id, carrier, recipient, postal_code, country, parcels, ship_date) "
                + "VALUES (?,?,?,?,?,?,?)";
        Connection con = null;
        PreparedStatement ps = null;
        try {
            con = dataSource.getConnection();
            ps = con.prepareStatement(sql);
            ps.setLong(1, notice.getOrderId());
            ps.setString(2, notice.getCarrier().name());
            ps.setString(3, notice.getRecipient());
            ps.setString(4, notice.getPostalCode());
            ps.setString(5, notice.getCountryCode());
            ps.setInt(6, notice.getParcels());
            ps.setDate(7, Date.valueOf(notice.getShipDate()));
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new ShippingException("shipment of order " + notice.getOrderId() + " not saved", e);
        } finally {
            try {
                if (ps != null) {
                    ps.close();
                }
                if (con != null) {
                    con.close();
                }
            } catch (SQLException ignore) {
                // closing failed, nothing to add
            }
        }
    }

    public List<ShipmentNotice> findByShipDate(java.time.LocalDate day) {
        List<ShipmentNotice> list = new ArrayList<ShipmentNotice>();
        String sql = "SELECT order_id, carrier, recipient, postal_code, country, parcels FROM shipment WHERE ship_date = ?";
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setDate(1, Date.valueOf(day));
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    ShipmentNotice n = new ShipmentNotice();
                    n.setOrderId(rs.getLong(1));
                    n.setCarrier(Carrier.valueOf(rs.getString(2)));
                    n.setRecipient(rs.getString(3));
                    n.setPostalCode(rs.getString(4));
                    n.setCountryCode(rs.getString(5));
                    n.setParcels(rs.getInt(6));
                    n.setShipDate(day);
                    list.add(n);
                }
            }
        } catch (SQLException e) {
            throw new ShippingException("could not read shipments of " + day, e);
        }
        return list;
    }
}
