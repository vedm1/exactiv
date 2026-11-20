package org.example.harbour.invoice;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * A stored exchange rate for one day.
 */
public class ExchangeRate {

    private final String from;
    private final String to;
    private final LocalDate day;
    private final BigDecimal rate;

    public ExchangeRate(String from, String to, LocalDate day, BigDecimal rate) {
        this.from = from;
        this.to = to;
        this.day = day;
        this.rate = rate;
    }

    public String getFrom() {
        return from;
    }

    public String getTo() {
        return to;
    }

    public LocalDate getDay() {
        return day;
    }

    public BigDecimal getRate() {
        return rate;
    }

    @Override
    public String toString() {
        return from + "->" + to + " " + rate + " on " + day;
    }
}
