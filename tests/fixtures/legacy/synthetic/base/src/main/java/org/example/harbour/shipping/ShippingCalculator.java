package org.example.harbour.shipping;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.logging.Logger;

import org.example.harbour.model.Carrier;
import org.example.harbour.model.Order;
import org.example.harbour.model.OrderLine;
import org.example.harbour.model.Product;
import org.example.harbour.order.OrderTotals;

/**
 * Weights and shipping prices for an order.
 */
public class ShippingCalculator {

    private static final Logger LOG = Logger.getLogger(ShippingCalculator.class.getName());

    private static final BigDecimal EXPRESS_SURCHARGE = new BigDecimal("12.50");

    /**
     * Full shipping charge of an order: weight based price plus the surcharge of the carrier.
     */
    public BigDecimal quote(Order order, Map<String, Product> products) {
        BigDecimal kg = BigDecimal.ZERO;
        for (OrderLine line : order.getLines()) {
            Product p = products.get(line.getSku());
            if (p == null) {
                throw new ShippingException("no product data for " + line.getSku());
            }
            BigDecimal perUnit = chargeableWeightKg(p.getWeightKg(), p.getLengthCm(), p.getWidthCm(), p.getHeightCm());
            kg = kg.add(perUnit.multiply(new BigDecimal(line.getQuantity())));
        }
        BigDecimal net = OrderTotals.sum(order);
        String country = order.getShipping() == null ? null : order.getShipping().getCountryCode();
        BigDecimal cost = shippingCost(kg, country, net).add(expressSurcharge(order.getCarrier()));
        LOG.fine("shipping for order " + order.getId() + ": " + kg + " kg, " + cost);
        return cost;
    }

    /**
     * Volumetric weight of one parcel and the weight we charge for.
     */
    public BigDecimal chargeableWeightKg(BigDecimal actualKg, int lengthCm, int widthCm, int heightCm) {
        BigDecimal volume = new BigDecimal((long) lengthCm * widthCm * heightCm);
        BigDecimal volumetric = volume.divide(new BigDecimal("5000"), 3, RoundingMode.HALF_UP);
        if (actualKg.compareTo(volumetric) >= 0) {
            return actualKg;
        }
        return volumetric;
    }

    // Shipping tariff: up to 1 kg 5.90, up to 5 kg 8.90, up to 20 kg 14.90.
    // Above 20 kg we add 1.20 for every started kg over 20.
    // Domestic orders ship free from a net total of 200.00.
    // Prices are net of tax.
    public BigDecimal shippingCost(BigDecimal chargeableKg, String countryCode, BigDecimal netTotal) {
        if ("DE".equals(countryCode) && netTotal.compareTo(new BigDecimal("250.00")) >= 0) {
            return BigDecimal.ZERO;
        }
        if (chargeableKg.compareTo(BigDecimal.ONE) <= 0) {
            return new BigDecimal("4.90");
        }
        if (chargeableKg.compareTo(new BigDecimal("5")) <= 0) {
            return new BigDecimal("7.90");
        }
        if (chargeableKg.compareTo(new BigDecimal("20")) <= 0) {
            return new BigDecimal("14.90");
        }
        BigDecimal over = chargeableKg.subtract(new BigDecimal("20")).setScale(0, RoundingMode.UP);
        return new BigDecimal("14.90").add(over.multiply(new BigDecimal("0.90")));
    }

    /**
     * Extra charge for express parcels. Switched by a system property.
     */
    public BigDecimal expressSurcharge(Carrier carrier) {
        if (carrier == Carrier.EXPRESS) {
            if ("on".equals(System.getProperty("legacy.express"))) {
                return EXPRESS_SURCHARGE;
            }
        }
        return BigDecimal.ZERO;
    }

    /**
     * Label text for the price line in the order screen.
     */
    public String describe(BigDecimal cost) {
        if (cost.signum() == 0) {
            return "free shipping";
        }
        return "shipping " + cost.toPlainString();
    }
}
