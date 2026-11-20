package org.example.harbour.invoice;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.example.harbour.model.Address;
import org.example.harbour.model.Customer;
import org.example.harbour.model.Invoice;
import org.example.harbour.model.InvoiceLine;
import org.example.harbour.model.InvoiceStatus;
import org.example.harbour.model.OrderLine;
import org.example.harbour.model.Product;
import org.example.harbour.pricing.LineResult;
import org.example.harbour.pricing.Money;
import org.example.harbour.pricing.PricingService;
import org.example.harbour.tax.TaxResult;
import org.example.harbour.tax.TaxService;

/**
 * Builds, issues and settles invoices.
 */
public class InvoiceService {

    private static final Logger LOG = Logger.getLogger(InvoiceService.class.getName());

    private final PricingService pricing;
    private final TaxService taxes;
    private final InvoiceDao dao;
    private final InvoiceNumberGenerator numbers;
    private final DueDateCalculator dueDates = new DueDateCalculator();
    private final LateFeeCalculator lateFees = new LateFeeCalculator();

    public InvoiceService(PricingService pricing, TaxService taxes, InvoiceDao dao,
            InvoiceNumberGenerator numbers) {
        this.pricing = pricing;
        this.taxes = taxes;
        this.dao = dao;
        this.numbers = numbers;
    }

    /**
     * Creates a draft invoice from order lines. Nothing is stored yet.
     */
    public Invoice createDraft(Customer customer, Address shipTo, List<OrderLine> orderLines,
            Map<String, Product> products, LocalDate issueDate) {
        Invoice inv = new Invoice();
        inv.setCustomerId(customer.getId());
        inv.setIssueDate(issueDate);
        inv.setDueDate(dueDates.dueDate(customer, issueDate));

        List<LineResult> priced = pricing.priceLines(customer, orderLines);
        List<String> categories = new ArrayList<String>();
        for (OrderLine ol : orderLines) {
            Product p = products.get(ol.getSku());
            categories.add(p == null ? null : p.getCategory());
        }
        List<TaxResult> lineTaxes = taxes.taxForLines(customer, shipTo.getCountryCode(), categories, priced);

        List<InvoiceLine> lines = new ArrayList<InvoiceLine>();
        for (int i = 0; i < priced.size(); i++) {
            LineResult r = priced.get(i);
            InvoiceLine il = new InvoiceLine();
            il.setSku(r.getSku());
            il.setQuantity(r.getQuantity());
            il.setNet(r.getNet());
            il.setTaxRate(lineTaxes.get(i).getRate());
            lines.add(il);
        }
        inv.setLines(lines);

        BigDecimal net = Money.ZERO;
        for (LineResult r : priced) {
            net = net.add(r.getNet());
        }
        BigDecimal tax = taxes.sumTax(lineTaxes);
        inv.setNet(net);
        inv.setTax(tax);
        inv.setTotal(computeTotal(net, tax, customer));
        return inv;
    }

    public BigDecimal computeTotal(BigDecimal net, BigDecimal tax, Customer customer) {
        BigDecimal credit = customer.getCreditBalance() == null ? BigDecimal.ZERO : customer.getCreditBalance();
        BigDecimal total = net.add(tax).subtract(credit);
        if (total.signum() < 0) {
            return Money.ZERO;
        }
        return Money.roundLine(total);
    }

    /**
     * Gives the draft a number and stores it as ISSUED.
     */
    public Invoice issue(Invoice draft) {
        InvoiceStateMachine.move(draft, InvoiceStatus.ISSUED);
        draft.setNumber(numbers.nextNumber(draft.getIssueDate().getYear()));
        try {
            dao.insert(draft);
        } catch (InvoiceException e) {
            draft.setStatus(InvoiceStatus.DRAFT);
            throw e;
        }
        LOG.info("issued " + draft.getNumber());
        return draft;
    }

    /**
     * Marks open invoices past their due date as OVERDUE and books the late fee.
     *
     * @return how many invoices changed
     */
    public int markOverdue(List<Invoice> openInvoices, LocalDate today) {
        int changed = 0;
        for (Invoice inv : openInvoices) {
            if (inv.getStatus() != InvoiceStatus.ISSUED) {
                continue;
            }
            if (!dueDates.isOverdue(inv.getDueDate(), today)) {
                continue;
            }
            try {
                InvoiceStateMachine.move(inv, InvoiceStatus.OVERDUE);
                inv.setLateFee(lateFees.lateFee(inv, today));
                dao.updateStatus(inv.getId(), InvoiceStatus.OVERDUE);
                changed++;
            } catch (InvoiceException e) {
                LOG.log(Level.WARNING, "could not mark overdue: " + inv.getNumber(), e);
            }
        }
        return changed;
    }

    public void markPaid(Invoice inv) {
        InvoiceStateMachine.move(inv, InvoiceStatus.PAID);
        dao.updateStatus(inv.getId(), InvoiceStatus.PAID);
    }

    // not used since the 2019 pricing change, kept until finance confirms
    private BigDecimal oldSeasonRebate(BigDecimal net, LocalDate issueDate) {
        BigDecimal rebate = BigDecimal.ZERO;
        int month = issueDate.getMonthValue();
        if (month == 12 || month == 1) {
            rebate = net.multiply(new BigDecimal("0.07"));
            if (net.compareTo(new BigDecimal("1000.00")) > 0) {
                rebate = rebate.add(new BigDecimal("25.00"));
            }
        }
        if (rebate.compareTo(new BigDecimal("150.00")) > 0) {
            rebate = new BigDecimal("150.00");
        }
        return Money.roundLine(rebate);
    }

    public List<Invoice> openInvoices(long customerId) {
        return dao.findOpenByCustomer(customerId);
    }
}
