package org.example.harbour.tax;

import java.io.Serializable;
import java.math.BigDecimal;

/**
 * Tax worked out for one line or one invoice.
 */
public class TaxResult implements Serializable {

    private static final long serialVersionUID = 1L;

    private final BigDecimal rate;
    private final BigDecimal amount;
    private final boolean reverseCharge;

    public TaxResult(BigDecimal rate, BigDecimal amount, boolean reverseCharge) {
        this.rate = rate;
        this.amount = amount;
        this.reverseCharge = reverseCharge;
    }

    public BigDecimal getRate() {
        return rate;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public boolean isReverseCharge() {
        return reverseCharge;
    }

    public BigDecimal getRatePercent() {
        return rate.multiply(new BigDecimal("100")).stripTrailingZeros();
    }

    @Override
    public String toString() {
        return "TaxResult{rate=" + rate + ", amount=" + amount
                + (reverseCharge ? ", reverse charge" : "") + "}";
    }
}
