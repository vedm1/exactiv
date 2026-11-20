package org.example.harbour.legacy;

import java.math.BigDecimal;

/**
 * Year-end bonus on turnover. Replaced by the loyalty tiers, nothing calls it any more.
 */
public class LegacyBonusCalc {

    public static BigDecimal bonusFor(BigDecimal yearTurnover) {
        if (yearTurnover.compareTo(new BigDecimal("100000")) >= 0) {
            return yearTurnover.multiply(new BigDecimal("0.03"));
        }
        if (yearTurnover.compareTo(new BigDecimal("40000")) >= 0) {
            return yearTurnover.multiply(new BigDecimal("0.015"));
        }
        return BigDecimal.ZERO;
    }
}
