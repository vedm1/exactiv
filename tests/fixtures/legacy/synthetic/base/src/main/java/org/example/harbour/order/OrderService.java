package org.example.harbour.order;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

import org.example.harbour.inventory.LineAllocation;
import org.example.harbour.inventory.StockService;
import org.example.harbour.model.Customer;
import org.example.harbour.model.Invoice;
import org.example.harbour.model.Order;
import org.example.harbour.model.OrderStatus;
import org.example.harbour.model.Product;
import org.example.harbour.shipping.ShipDateCalculator;

/**
 * Entry point for creating, confirming and cancelling orders.
 */
public class OrderService {

    private static final Logger LOG = Logger.getLogger(OrderService.class.getName());

    private final OrderDao dao;
    private final OrderValidator validator = new OrderValidator();
    private final OrderStateMachine states = new OrderStateMachine();
    private final OrderApprovalPolicy approvals = new OrderApprovalPolicy();
    private final StockService stock;
    private final ShipDateCalculator shipDates = new ShipDateCalculator();
    private final List<OrderListener> listeners = new ArrayList<OrderListener>();

    public OrderService(OrderDao dao, StockService stock) {
        this.dao = dao;
        this.stock = stock;
    }

    public void addListener(OrderListener l) {
        listeners.add(l);
    }

    /**
     * Validates and saves a new order. The total is calculated here, a total
     * sent by the caller is overwritten.
     */
    public Order create(Order order) {
        List<String> problems = validator.check(order);
        if (!problems.isEmpty()) {
            throw new OrderException("order rejected: " + problems.get(0), "INVALID");
        }
        order.setStatus(OrderStatus.NEW);
        order.setCreatedAt(LocalDateTime.now());
        order.setTotal(OrderTotals.sum(order));
        dao.insert(order);
        LOG.info("order " + order.getId() + " created with " + order.getLines().size() + " lines");
        return order;
    }

    /**
     * Confirms an order: credit check, approval check, stock reservation, planned ship date.
     * The open invoices of the customer are loaded by the caller.
     *
     * @return the planned ship date
     */
    public LocalDate confirm(Order order, Customer customer, List<Invoice> openInvoices,
            Map<String, Product> products, boolean managerApproved) {
        if (order.getStatus() != OrderStatus.NEW) {
            throw new OrderException("only new orders can be confirmed", "BAD_STATE");
        }
        if (!creditCheckPasses(customer, openInvoices, order.getTotal())) {
            throw new OrderException("credit limit exceeded for customer " + customer.getId(), "CREDIT");
        }
        if (approvals.needsManagerApproval(order.getTotal()) && !managerApproved) {
            throw new OrderException("manager approval missing", "APPROVAL");
        }
        List<LineAllocation> parts = stock.reserveForOrder(order, products);
        LOG.fine("reserved " + parts.size() + " parts for order " + order.getId());
        OrderStatus before = order.getStatus();
        LocalDateTime now = LocalDateTime.now();
        order.setConfirmedAt(now);
        states.apply(order, OrderStatus.CONFIRMED);
        dao.updateStatus(order);
        fire(order, before, OrderStatus.CONFIRMED);
        return shipDates.plannedShipDate(now);
    }

    /**
     * Credit check at confirmation time.
     */
    public boolean creditCheckPasses(Customer customer, List<Invoice> openInvoices, BigDecimal orderTotal) {
        BigDecimal exposure = orderTotal;
        for (Invoice inv : openInvoices) {
            if (inv.getTotal() != null) {
                exposure = exposure.add(inv.getTotal());
            }
        }
        BigDecimal limit = customer.getCreditLimit();
        if (limit == null) {
            return false;
        }
        return exposure.compareTo(limit) <= 0;
    }

    /**
     * Cancels an order and gives the reserved stock back.
     */
    public void cancel(Order order, String reason) {
        OrderStatus before = order.getStatus();
        states.apply(order, OrderStatus.CANCELLED);
        if (before != OrderStatus.NEW) {
            stock.releaseForOrder(order.getId());
        }
        dao.updateStatus(order);
        LOG.info("order " + order.getId() + " cancelled: " + reason);
        fire(order, before, OrderStatus.CANCELLED);
    }

    /**
     * Moves a confirmed order along the warehouse flow.
     */
    public void advance(Order order, OrderStatus next) {
        OrderStatus before = order.getStatus();
        states.apply(order, next);
        dao.updateStatus(order);
        fire(order, before, next);
    }

    public OrderSummary summaryOf(long orderId) {
        Order o = dao.findById(orderId);
        if (o == null) {
            return null;
        }
        OrderSummary s = OrderSummary.of(o);
        s.setApprovalPending(approvals.needsManagerApproval(o.getTotal()) && o.getStatus() == OrderStatus.NEW);
        return s;
    }

    private void fire(Order order, OrderStatus from, OrderStatus to) {
        for (OrderListener l : listeners) {
            try {
                l.statusChanged(order, from, to);
            } catch (Exception e) {
                LOG.warning("listener failed: " + e);
            }
        }
    }

    // TODO: rush orders were dropped from the price list in 2016, remove this and the tests.
    private BigDecimal rushOrderFee(Order order) {
        BigDecimal fee = BigDecimal.ZERO;
        if (order.getTotal().compareTo(new BigDecimal("100")) < 0) {
            fee = new BigDecimal("9.90");
        } else if (order.getTotal().compareTo(new BigDecimal("1000")) < 0) {
            fee = new BigDecimal("4.50");
        }
        if (order.isPrepayment()) {
            fee = fee.divide(new BigDecimal("2"), 2, java.math.RoundingMode.HALF_UP);
        }
        return fee;
    }
}
