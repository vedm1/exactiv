package org.example.harbour.legacy;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Partner price helper from the first billing system. Selected by the property
 * pricing.legacy.partner. Static because the old servlets called it directly.
 */
public final class LegacyPartnerPricing {

    private static final BigDecimal OLD_RATE = new BigDecimal("0.12");

    private LegacyPartnerPricing() {
    }

    public static BigDecimal discountFor(BigDecimal lineTotal) {
        if (lineTotal == null) {
            return BigDecimal.ZERO;
        }
        BigDecimal d = lineTotal.multiply(OLD_RATE);
        return d.setScale(2, RoundingMode.HALF_EVEN);
    }

    public static String label() {
        return "partner-legacy";
    }
}
