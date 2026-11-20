package org.example.harbour.invoice;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import javax.sql.DataSource;

/**
 * JDBC access to the exchange_rate table.
 */
public class ExchangeRateDao implements RateSource {

    private final DataSource dataSource;

    public ExchangeRateDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public ExchangeRate findOn(String from, String to, LocalDate day) {
        return queryOne("SELECT rate_day, rate FROM exchange_rate WHERE from_ccy = ? AND to_ccy = ? AND rate_day = ?",
                from, to, day);
    }

    @Override
    public ExchangeRate findLatestBefore(String from, String to, LocalDate day) {
        return queryOne("SELECT rate_day, rate FROM exchange_rate WHERE from_ccy = ? AND to_ccy = ? AND rate_day < ? "
                + "ORDER BY rate_day DESC FETCH FIRST 1 ROWS ONLY", from, to, day);
    }

    private ExchangeRate queryOne(String sql, String from, String to, LocalDate day) {
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setString(1, from);
            ps.setString(2, to);
            ps.setDate(3, Date.valueOf(day));
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return null;
                }
                return new ExchangeRate(from, to, rs.getDate(1).toLocalDate(), rs.getBigDecimal(2));
            }
        } catch (SQLException e) {
            throw new InvoiceException("exchange rate lookup failed", e);
        }
    }

    public void store(ExchangeRate r) {
        String sql = "INSERT INTO exchange_rate (from_ccy, to_ccy, rate_day, rate) VALUES (?, ?, ?, ?)";
        try (Connection con = dataSource.getConnection();
                PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setString(1, r.getFrom());
            ps.setString(2, r.getTo());
            ps.setDate(3, Date.valueOf(r.getDay()));
            ps.setBigDecimal(4, r.getRate());
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new InvoiceException("exchange rate store failed", e);
        }
    }
}
