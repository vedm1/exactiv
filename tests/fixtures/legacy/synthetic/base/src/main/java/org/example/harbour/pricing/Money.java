package org.example.harbour.pricing;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Rounding helpers for money values. All amounts in the system have two decimals.
 */
public final class Money {

    public static final BigDecimal ZERO = new BigDecimal("0.00");
    public static final BigDecimal HUNDRED = new BigDecimal("100");
    private static final int SCALE = 2;

    private Money() {
    }

    public static BigDecimal roundLine(BigDecimal value) {
        if (value == null) {
            return ZERO;
        }
        return value.setScale(SCALE, RoundingMode.HALF_EVEN);
    }

    /**
     * Sum of already rounded amounts. Does not round again.
     */
    public static BigDecimal sum(Iterable<BigDecimal> amounts) {
        BigDecimal total = ZERO;
        for (BigDecimal a : amounts) {
            if (a != null) {
                total = total.add(a);
            }
        }
        return total;
    }

    public static BigDecimal percentOf(BigDecimal base, BigDecimal percent) {
        return base.multiply(percent).divide(HUNDRED);
    }

    public static boolean isNegative(BigDecimal value) {
        return value != null && value.signum() < 0;
    }

    public static BigDecimal max(BigDecimal a, BigDecimal b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    public static BigDecimal min(BigDecimal a, BigDecimal b) {
        return a.compareTo(b) <= 0 ? a : b;
    }

    public static String format(BigDecimal value) {
        return roundLine(value).toPlainString();
    }
}
