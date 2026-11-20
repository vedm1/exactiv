package org.example.harbour.audit;

import java.math.BigDecimal;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.example.harbour.model.User;

/**
 * Maintenance of price lists.
 */
public class PriceListService {

    private static final Logger LOG = Logger.getLogger(PriceListService.class.getName());

    private final AuditDao auditDao;

    public PriceListService(AuditDao auditDao) {
        this.auditDao = auditDao;
    }

    public void changePrice(User user, PriceList list, String sku, BigDecimal newPrice) throws SQLException {
        if (newPrice == null || newPrice.signum() < 0) {
            throw new IllegalArgumentException("price must not be negative");
        }
        BigDecimal oldPrice = list.priceOf(sku);
        list.put(sku, newPrice);
        String subject = "price:" + list.getName() + ":" + sku;
        String oldText = oldPrice == null ? "(none)" : oldPrice.toPlainString();
        AuditEntry entry = new AuditEntry(user.getName(), subject, oldText, newPrice.toPlainString(),
                LocalDateTime.now());
        auditDao.insert(entry);
        LOG.fine("price changed: " + entry);
    }

    /**
     * Loads many prices at once, for example from the supplier file. Each change is audited.
     * Returns the number of prices that were really different.
     */
    public int changePrices(User user, PriceList list, Map<String, BigDecimal> incoming) {
        int changed = 0;
        for (Map.Entry<String, BigDecimal> e : incoming.entrySet()) {
            BigDecimal current = list.priceOf(e.getKey());
            if (current != null && current.compareTo(e.getValue()) == 0) {
                continue;
            }
            try {
                changePrice(user, list, e.getKey(), e.getValue());
                changed++;
            } catch (Exception ex) {
                LOG.log(Level.SEVERE, "price change failed for " + e.getKey(), ex);
            }
        }
        return changed;
    }

    public PriceList create(long id, String name) {
        return new PriceList(id, name);
    }
}
