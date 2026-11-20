package org.example.harbour.pricing;

import java.io.Serializable;
import java.math.BigDecimal;

/**
 * Result of pricing one order line. Plain holder, filled by PricingService.
 */
public class LineResult implements Serializable {

    private static final long serialVersionUID = 1L;

    private String sku;
    private int quantity;
    private BigDecimal unitPrice = Money.ZERO;
    private BigDecimal gross = Money.ZERO;
    private BigDecimal volumeDiscount = Money.ZERO;
    private BigDecimal tierDiscount = Money.ZERO;
    private BigDecimal partnerDiscount = Money.ZERO;
    private BigDecimal totalDiscount = Money.ZERO;
    private BigDecimal net = Money.ZERO;

    public String getSku() {
        return sku;
    }

    public void setSku(String sku) {
        this.sku = sku;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    public BigDecimal getUnitPrice() {
        return unitPrice;
    }

    public void setUnitPrice(BigDecimal unitPrice) {
        this.unitPrice = unitPrice;
    }

    public BigDecimal getGross() {
        return gross;
    }

    public void setGross(BigDecimal gross) {
        this.gross = gross;
    }

    public BigDecimal getVolumeDiscount() {
        return volumeDiscount;
    }

    public void setVolumeDiscount(BigDecimal volumeDiscount) {
        this.volumeDiscount = volumeDiscount;
    }

    public BigDecimal getTierDiscount() {
        return tierDiscount;
    }

    public void setTierDiscount(BigDecimal tierDiscount) {
        this.tierDiscount = tierDiscount;
    }

    public BigDecimal getPartnerDiscount() {
        return partnerDiscount;
    }

    public void setPartnerDiscount(BigDecimal partnerDiscount) {
        this.partnerDiscount = partnerDiscount;
    }

    public BigDecimal getTotalDiscount() {
        return totalDiscount;
    }

    public void setTotalDiscount(BigDecimal totalDiscount) {
        this.totalDiscount = totalDiscount;
    }

    public BigDecimal getNet() {
        return net;
    }

    public void setNet(BigDecimal net) {
        this.net = net;
    }

    public boolean hasDiscount() {
        return totalDiscount.signum() > 0;
    }

    @Override
    public String toString() {
        StringBuffer sb = new StringBuffer();
        sb.append("LineResult[").append(sku);
        sb.append(" x").append(quantity);
        sb.append(" gross=").append(gross);
        sb.append(" discount=").append(totalDiscount);
        sb.append(" net=").append(net).append(']');
        return sb.toString();
    }
}
