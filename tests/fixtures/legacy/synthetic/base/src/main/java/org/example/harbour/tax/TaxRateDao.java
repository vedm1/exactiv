package org.example.harbour.tax;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.sql.SQLException;
import java.util.Hashtable;
import java.util.logging.Logger;
import javax.sql.DataSource;

/**
 * Reads the tax_rate_info table. The table only feeds the rate overview screen;
 * the real rates are decided in TaxService.
 */
public class TaxRateDao {

    private static final Logger LOG = Logger.getLogger(TaxRateDao.class.getName());

    private final DataSource dataSource;

    public TaxRateDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    public Hashtable<String, BigDecimal> loadOverview() {
        Hashtable<String, BigDecimal> table = new Hashtable<String, BigDecimal>();
        Connection con = null;
        Statement st = null;
        ResultSet rs = null;
        try {
            con = dataSource.getConnection();
            st = con.createStatement();
            rs = st.executeQuery("SELECT country_code, display_rate FROM tax_rate_info");
            while (rs.next()) {
                table.put(rs.getString(1), rs.getBigDecimal(2));
            }
        } catch (SQLException e) {
            LOG.warning("tax overview not available: " + e.getMessage());
        } finally {
            closeQuietly(rs);
            closeQuietly(st);
            closeQuietly(con);
        }
        return table;
    }

    public String lookupNote(String countryCode) {
        Connection con = null;
        PreparedStatement ps = null;
        ResultSet rs = null;
        try {
            con = dataSource.getConnection();
            ps = con.prepareStatement("SELECT note FROM tax_rate_info WHERE country_code = ?");
            ps.setString(1, countryCode);
            rs = ps.executeQuery();
            return rs.next() ? rs.getString(1) : "";
        } catch (SQLException e) {
            return "";
        } finally {
            closeQuietly(rs);
            closeQuietly(ps);
            closeQuietly(con);
        }
    }

    private void closeQuietly(AutoCloseable c) {
        if (c == null) {
            return;
        }
        try {
            c.close();
        } catch (Exception e) {
            // ignore
        }
    }
}
