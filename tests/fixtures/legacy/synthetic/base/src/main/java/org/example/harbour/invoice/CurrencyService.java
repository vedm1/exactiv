package org.example.harbour.invoice;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.logging.Logger;

import org.example.harbour.pricing.Money;
import org.example.harbour.util.Dates;

/**
 * Converts amounts between currencies with the stored daily rates.
 */
public class CurrencyService {

    private static final Logger LOG = Logger.getLogger(CurrencyService.class.getName());

    private static final int MAX_RATE_AGE_DAYS = 3;

    private final RateSource rates;

    public CurrencyService(RateSource rates) {
        this.rates = rates;
    }

    public BigDecimal convert(BigDecimal amount, String from, String to, LocalDate day) {
        if (from.equals(to)) {
            return amount;
        }
        ExchangeRate rate = rates.findOn(from, to, day);
        if (rate == null) {
            ExchangeRate last = rates.findLatestBefore(from, to, day);
            if (last == null || Dates.daysBetween(last.getDay(), day) > MAX_RATE_AGE_DAYS) {
                throw new RateUnavailableException("no rate " + from + "->" + to + " for " + day);
            }
            LOG.info("using older rate from " + last.getDay());
            rate = last;
        }
        return Money.roundLine(amount.multiply(rate.getRate()));
    }

    public BigDecimal toEuro(BigDecimal amount, String currency, LocalDate day) {
        return convert(amount, currency, "EUR", day);
    }
}
