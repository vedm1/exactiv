package org.example.harbour.pricing;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.sql.DataSource;

/**
 * Reads list prices from the price_list table.
 */
public class PriceListDao {

    private static final Logger LOG = Logger.getLogger(PriceListDao.class.getName());

    private static final String SELECT_ONE =
            "SELECT unit_price FROM price_list WHERE sku = ? AND active = 1";
    private static final String SELECT_BY_CATEGORY =
            "SELECT sku, unit_price FROM price_list WHERE category = ? AND active = 1 ORDER BY sku";
    private static final String SELECT_SKUS =
            "SELECT sku FROM price_list WHERE active = 1 ORDER BY sku";

    private final DataSource dataSource;

    public PriceListDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * @return the active list price or null when the sku is not listed
     */
    public BigDecimal findUnitPrice(String sku) {
        Connection con = null;
        PreparedStatement ps = null;
        ResultSet rs = null;
        try {
            con = dataSource.getConnection();
            ps = con.prepareStatement(SELECT_ONE);
            ps.setString(1, sku);
            rs = ps.executeQuery();
            if (rs.next()) {
                return rs.getBigDecimal(1);
            }
            return null;
        } catch (SQLException e) {
            LOG.log(Level.SEVERE, "price lookup failed for " + sku, e);
            throw new PricingException("price lookup failed", e);
        } finally {
            close(rs, ps, con);
        }
    }

    public Map<String, BigDecimal> findByCategory(String category) {
        Map<String, BigDecimal> result = new HashMap<String, BigDecimal>();
        Connection con = null;
        PreparedStatement ps = null;
        ResultSet rs = null;
        try {
            con = dataSource.getConnection();
            ps = con.prepareStatement(SELECT_BY_CATEGORY);
            ps.setString(1, category);
            rs = ps.executeQuery();
            while (rs.next()) {
                result.put(rs.getString("sku"), rs.getBigDecimal("unit_price"));
            }
        } catch (SQLException e) {
            LOG.log(Level.SEVERE, "category price lookup failed", e);
            throw new PricingException("category price lookup failed", e);
        } finally {
            close(rs, ps, con);
        }
        return result;
    }

    public List<String> listSkus() {
        List<String> skus = new ArrayList<String>();
        Connection con = null;
        PreparedStatement ps = null;
        ResultSet rs = null;
        try {
            con = dataSource.getConnection();
            ps = con.prepareStatement(SELECT_SKUS);
            rs = ps.executeQuery();
            while (rs.next()) {
                skus.add(rs.getString(1));
            }
        } catch (SQLException e) {
            // TODO return an empty list instead of failing the whole screen?
            throw new PricingException("sku listing failed", e);
        } finally {
            close(rs, ps, con);
        }
        return skus;
    }

    private void close(ResultSet rs, PreparedStatement ps, Connection con) {
        try {
            if (rs != null) {
                rs.close();
            }
        } catch (SQLException ignore) {
            // ignored
        }
        try {
            if (ps != null) {
                ps.close();
            }
        } catch (SQLException ignore) {
            // ignored
        }
        try {
            if (con != null) {
                con.close();
            }
        } catch (SQLException ignore) {
            // ignored
        }
    }
}
