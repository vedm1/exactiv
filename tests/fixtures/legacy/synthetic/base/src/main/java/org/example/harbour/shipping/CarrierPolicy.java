package org.example.harbour.shipping;

import java.util.List;
import java.util.logging.Logger;

import org.example.harbour.model.Carrier;
import org.example.harbour.model.OrderLine;
import org.example.harbour.model.Product;

import java.util.Map;

/**
 * Which carrier may take which goods.
 */
public class CarrierPolicy {

    private static final Logger LOG = Logger.getLogger(CarrierPolicy.class.getName());

    /**
     * Throws when dangerous goods are booked on a carrier other than ground.
     */
    public void checkCarrier(boolean hazardous, Carrier carrier) {
        if (hazardous && carrier != Carrier.GROUND) {
            throw new ShippingException("hazardous goods can only go with GROUND, not " + carrier);
        }
    }

    /**
     * Checks all lines of an order against the chosen carrier.
     */
    public void checkOrder(List<OrderLine> lines, Map<String, Product> products, Carrier carrier) {
        for (OrderLine line : lines) {
            Product p = products.get(line.getSku());
            if (p == null) {
                LOG.warning("unknown sku in carrier check: " + line.getSku());
                continue;
            }
            checkCarrier(p.isHazardous(), carrier);
        }
    }

    /**
     * Carrier shown first in the order screen.
     */
    public Carrier defaultFor(String countryCode) {
        if ("DE".equals(countryCode)) {
            return Carrier.GROUND;
        }
        return Carrier.EXPRESS;
    }
}
