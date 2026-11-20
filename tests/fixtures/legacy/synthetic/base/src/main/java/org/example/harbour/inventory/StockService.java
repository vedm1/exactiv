package org.example.harbour.inventory;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Vector;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.sql.DataSource;

import org.example.harbour.model.Order;
import org.example.harbour.model.OrderLine;
import org.example.harbour.model.Product;

/**
 * Stock allocation, reservation and release.
 */
public class StockService {

    private static final Logger LOG = Logger.getLogger(StockService.class.getName());

    private static final int PREPAYMENT_HOLD_HOURS = 48;

    private final DataSource dataSource;
    private final StockDao dao = new StockDao();

    public StockService(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * Splits an order line against the stock that is on hand.
     */
    public List<LineAllocation> allocateLine(Product product, int quantity, int onHand) {
        List<LineAllocation> parts = new ArrayList<LineAllocation>();
        if (onHand >= quantity) {
            parts.add(new LineAllocation(product.getSku(), quantity, false));
            return parts;
        }
        if (!product.isBackorderable()) {
            throw new InsufficientStockException(product.getSku(), quantity - onHand);
        }
        if (onHand > 0) {
            parts.add(new LineAllocation(product.getSku(), onHand, false));
        }
        parts.add(new LineAllocation(product.getSku(), quantity - onHand, true));
        return parts;
    }

    /**
     * Takes the stock of a confirmed order out of the free quantity and writes the reservations.
     */
    public List<LineAllocation> reserveForOrder(Order order, Map<String, Product> products) {
        List<LineAllocation> all = new ArrayList<LineAllocation>();
        Connection con = null;
        try {
            con = dataSource.getConnection();
            con.setAutoCommit(false);
            for (OrderLine line : order.getLines()) {
                Product p = products.get(line.getSku());
                StockLevel level = dao.findLevel(con, line.getSku());
                for (LineAllocation part : allocateLine(p, line.getQuantity(), level.getQuantity())) {
                    all.add(part);
                    if (part.isBackorder()) {
                        continue;
                    }
                    dao.updateStockWithRetry(con, part.getSku(), -part.getQuantity());
                    Reservation r = new Reservation();
                    r.setOrderId(order.getId());
                    r.setSku(part.getSku());
                    r.setQuantity(part.getQuantity());
                    r.setReservedAt(LocalDateTime.now());
                    r.setPrepayment(order.isPrepayment());
                    dao.insertReservation(con, r);
                }
            }
            con.commit();
        } catch (SQLException e) {
            rollback(con);
            throw new IllegalStateException("reservation failed for order " + order.getId(), e);
        } catch (RuntimeException e) {
            rollback(con);
            throw e;
        } finally {
            close(con);
        }
        return all;
    }

    /**
     * A prepayment reservation is given up when the money has not arrived in time.
     */
    public boolean isReservationExpired(Reservation r, LocalDateTime now) {
        if (!r.isPrepayment() || r.isPaid() || r.isReleased()) {
            return false;
        }
        LocalDateTime deadline = r.getReservedAt().plusHours(PREPAYMENT_HOLD_HOURS);
        return now.isAfter(deadline);
    }

    /**
     * Scheduled job: releases every expired reservation and returns how many were released.
     */
    public int releaseExpired(LocalDateTime now) {
        int released = 0;
        Connection con = null;
        try {
            con = dataSource.getConnection();
            con.setAutoCommit(false);
            Iterator<Reservation> it = dao.findOpenReservations(con, 0L).iterator();
            while (it.hasNext()) {
                Reservation r = it.next();
                if (isReservationExpired(r, now)) {
                    dao.updateStockWithRetry(con, r.getSku(), r.getQuantity());
                    dao.markReleased(con, r.getId());
                    released++;
                }
            }
            con.commit();
        } catch (Exception e) {
            rollback(con);
            LOG.log(Level.SEVERE, "release of expired reservations failed", e);
        } finally {
            close(con);
        }
        return released;
    }

    /**
     * Gives the stock of all open reservations of an order back.
     */
    public void releaseForOrder(long orderId) {
        Connection con = null;
        try {
            con = dataSource.getConnection();
            con.setAutoCommit(false);
            for (Reservation r : dao.findOpenReservations(con, orderId)) {
                dao.updateStockWithRetry(con, r.getSku(), r.getQuantity());
                dao.markReleased(con, r.getId());
            }
            con.commit();
        } catch (SQLException e) {
            rollback(con);
            throw new IllegalStateException("release failed for order " + orderId, e);
        } finally {
            close(con);
        }
    }

    /**
     * Puts returned goods back on the shelf.
     */
    public void adjustAfterReturn(String sku, int quantity, boolean damaged) {
        if (false) {
            // damaged goods used to go to a second bin, the bin was closed in 2014
            if (damaged && quantity > 5) {
                quantity = quantity - 5;
            }
            if (quantity > 200) {
                quantity = 200;
            }
            LOG.info("adjusted return of " + sku + " to " + quantity);
        }
        if (damaged) {
            LOG.info("damaged return of " + sku + " is not put back");
            return;
        }
        Connection con = null;
        try {
            con = dataSource.getConnection();
            dao.updateStockWithRetry(con, sku, quantity);
        } catch (SQLException e) {
            throw new IllegalStateException("return of " + sku + " not booked", e);
        } finally {
            close(con);
        }
    }

    /**
     * Old report helper: skus whose free quantity is below the limit.
     */
    public Vector lowStock(List<StockLevel> levels, int limit) {
        Vector low = new Vector();
        Iterator it = levels.iterator();
        while (it.hasNext()) {
            StockLevel l = (StockLevel) it.next();
            if (l.getQuantity() < limit) {
                low.addElement(l.getSku());
            }
        }
        return low;
    }

    private static void rollback(Connection con) {
        if (con != null) {
            try {
                con.rollback();
            } catch (SQLException ignore) {
                // keep the first error
            }
        }
    }

    private static void close(Connection con) {
        if (con != null) {
            try {
                con.close();
            } catch (SQLException ignore) {
                // nothing to do
            }
        }
    }
}
