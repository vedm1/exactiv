package org.example.harbour.invoice;

import java.time.LocalDate;

/**
 * Where exchange rates come from. The database version is ExchangeRateDao.
 */
public interface RateSource {

    /**
     * @return the rate stored for exactly this day, or null
     */
    ExchangeRate findOn(String from, String to, LocalDate day);

    /**
     * @return the newest rate stored before this day, or null
     */
    ExchangeRate findLatestBefore(String from, String to, LocalDate day);
}
