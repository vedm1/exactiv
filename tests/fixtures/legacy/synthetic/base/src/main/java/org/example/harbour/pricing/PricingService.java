package org.example.harbour.pricing;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Vector;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;

import org.example.harbour.legacy.LegacyPartnerPricing;
import org.example.harbour.model.Customer;
import org.example.harbour.model.CustomerTier;
import org.example.harbour.model.OrderLine;
import org.example.harbour.util.Config;

/**
 * Prices order lines: discounts, caps and rounding.
 *
 * Order of work for one line: gross, volume discount, tier discount,
 * partner discount, cap, group adjustment.
 */
public class PricingService {

    private static final Logger LOG = Logger.getLogger(PricingService.class.getName());

    private static final BigDecimal MAX_DISCOUNT_SHARE = new BigDecimal("0.25");
    private static final BigDecimal PARTNER_RATE = new BigDecimal("0.10");
    private static final String PARTNER_HELPER_KEY = "pricing.legacy.partner";

    private final PriceListDao priceListDao;

    public PricingService(PriceListDao priceListDao) {
        this.priceListDao = priceListDao;
    }

    /**
     * Prices one line for a customer.
     */
    public LineResult priceLine(Customer customer, String sku, int quantity, BigDecimal unitPrice) {
        if (unitPrice == null) {
            throw new PricingException("no unit price for " + sku);
        }
        BigDecimal gross = Money.roundLine(unitPrice.multiply(BigDecimal.valueOf(quantity)));
        BigDecimal volume = volumeDiscount(gross, quantity);
        BigDecimal afterVolume = gross.subtract(volume);

        CustomerTier tier = customer == null ? CustomerTier.STANDARD : customer.getTier();
        BigDecimal tierPart = tierDiscount(tier, afterVolume);
        BigDecimal afterTier = afterVolume.subtract(tierPart);

        BigDecimal partnerPart = partnerDiscount(customer, afterTier);
        BigDecimal wanted = volume.add(tierPart).add(partnerPart);
        BigDecimal granted = capDiscount(gross, wanted);

        BigDecimal net = Money.roundLine(gross.subtract(granted));
        net = adjustForGroup(customer, net);

        LineResult r = new LineResult();
        r.setSku(sku);
        r.setQuantity(quantity);
        r.setUnitPrice(unitPrice);
        r.setGross(gross);
        r.setVolumeDiscount(volume);
        r.setTierDiscount(tierPart);
        r.setPartnerDiscount(partnerPart);
        r.setTotalDiscount(granted);
        r.setNet(net);
        if (LOG.isLoggable(Level.FINE)) {
            LOG.fine("priced " + r);
        }
        return r;
    }

    /**
     * Prices all lines of an order. Unit prices come from the order line,
     * or from the price list when the order line has none.
     */
    public List<LineResult> priceLines(Customer customer, List<OrderLine> lines) {
        return lines.stream()
                .map(l -> priceLine(customer, l.getSku(), l.getQuantity(), resolveUnitPrice(l)))
                .collect(Collectors.toList());
    }

    private BigDecimal resolveUnitPrice(OrderLine line) {
        if (line.getUnitPrice() != null) {
            return line.getUnitPrice();
        }
        return priceListDao.findUnitPrice(line.getSku());
    }

    /**
     * Volume discount of a line, taken from the gross amount.
     */
    public BigDecimal volumeDiscount(BigDecimal gross, int quantity) {
        BigDecimal rate;
        if (quantity >= 200) {
            rate = new BigDecimal("0.20");
        } else if (quantity >= 50) {
            rate = new BigDecimal("0.12");
        } else if (quantity >= 10) {
            rate = new BigDecimal("0.05");
        } else {
            rate = BigDecimal.ZERO;
        }
        return Money.roundLine(gross.multiply(rate));
    }

    public BigDecimal tierDiscount(CustomerTier tier, BigDecimal amountAfterVolume) {
        BigDecimal rate = BigDecimal.ZERO;
        if (tier == CustomerTier.GOLD) {
            rate = new BigDecimal("0.08");
        } else if (tier == CustomerTier.SILVER) {
            rate = new BigDecimal("0.04");
        }
        return Money.roundLine(amountAfterVolume.multiply(rate));
    }

    public BigDecimal capDiscount(BigDecimal gross, BigDecimal totalDiscount) {
        BigDecimal ceiling = Money.roundLine(gross.multiply(MAX_DISCOUNT_SHARE));
        if (totalDiscount.compareTo(ceiling) > 0) {
            LOG.fine("discount capped at " + ceiling);
            return ceiling;
        }
        return Money.roundLine(totalDiscount);
    }

    public BigDecimal partnerDiscount(Customer customer, BigDecimal lineTotal) {
        if (customer == null || !customer.isPartner()) {
            return Money.ZERO;
        }
        if (Config.getBool(PARTNER_HELPER_KEY, false)) {
            return LegacyPartnerPricing.discountFor(lineTotal);
        }
        return Money.roundLine(lineTotal.multiply(PARTNER_RATE));
    }

    public BigDecimal adjustForGroup(Customer customer, BigDecimal lineNet) {
        if (customer != null && customer.getGroupCode() == 7) {
            return Money.roundLine(lineNet.multiply(new BigDecimal("0.9625")));
        }
        return lineNet;
    }

    /**
     * Old summary routine, still used by the nightly export. Raw collections on purpose.
     */
    public BigDecimal sumNet(Vector results) {
        BigDecimal total = Money.ZERO;
        Iterator it = results.iterator();
        while (it.hasNext()) {
            LineResult r = (LineResult) it.next();
            total = total.add(r.getNet());
        }
        return total;
    }

    public List<String> describe(List<LineResult> results) {
        List<String> out = new ArrayList<String>();
        for (LineResult r : results) {
            out.add(r.getSku() + ": " + Money.format(r.getGross()) + " -> " + Money.format(r.getNet()));
        }
        return out;
    }

    /**
     * Cheapest and dearest list price in a category, for the catalogue page.
     */
    public BigDecimal[] priceRange(String category) {
        Map<String, BigDecimal> prices = priceListDao.findByCategory(category);
        BigDecimal low = null;
        BigDecimal high = null;
        for (BigDecimal p : prices.values()) {
            if (low == null || p.compareTo(low) < 0) {
                low = p;
            }
            if (high == null || p.compareTo(high) > 0) {
                high = p;
            }
        }
        // FIXME empty category returns nulls, callers must check
        return new BigDecimal[] {low, high};
    }
}
