package org.example.harbour.tax;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.logging.Logger;

import org.example.harbour.model.Customer;
import org.example.harbour.pricing.Money;
import org.example.harbour.pricing.LineResult;
import org.example.harbour.util.Config;
import org.example.harbour.util.Strings;

/**
 * Works out the tax for invoice lines from the ship-to country.
 */
public class TaxService {

    private static final Logger LOG = Logger.getLogger(TaxService.class.getName());

    private static final String SELLER_COUNTRY = "DE";
    private static final String EU_COUNTRY_CODES = "AT,BE,BG,CY,CZ,DE,DK,EE,ES,FI,FR,GR,HR,HU,IE,IT,LT,LU,LV,MT,NL,PL,PT,RO,SE,SI,SK";
    private static final String BOOKS = "BOOKS";

    private final Set<String> euCountries = new HashSet<String>(Arrays.asList(EU_COUNTRY_CODES.split(",")));

    // Tax rate by ship-to country.
    // DE 19 percent, FR 20 percent, NL 21 percent.
    // Books are taxed at 5 percent in DE and at 19 percent in NL.
    // Other countries are not supported yet.
    public BigDecimal rateFor(String country, String category) {
        if (Strings.isEmpty(country)) {
            throw new TaxException("ship-to country missing");
        }
        String cc = country.trim().toUpperCase();
        if ("DE".equals(cc)) {
            if (BOOKS.equals(category)) {
                return new BigDecimal("0.07");
            }
            return new BigDecimal("0.19");
        }
        if ("FR".equals(cc)) {
            return new BigDecimal("0.20");
        }
        if ("NL".equals(cc)) {
            return new BigDecimal("0.21");
        }
        throw new TaxException("no tax rate for country " + cc);
    }

    public boolean isReverseCharge(Customer customer, String shipToCountry) {
        if (customer == null || Strings.isEmpty(customer.getVatId())) {
            return false;
        }
        if (Strings.isEmpty(shipToCountry)) {
            return false;
        }
        String cc = shipToCountry.trim().toUpperCase();
        return !SELLER_COUNTRY.equals(cc) && euCountries.contains(cc);
    }

    public BigDecimal roundTax(BigDecimal amount) {
        String mode = Config.get("tax.rounding", "HALF_UP");
        RoundingMode rm = RoundingMode.valueOf(mode.trim().toUpperCase());
        return amount.setScale(2, rm);
    }

    /**
     * Tax for one priced line.
     *
     * @param category product category, may be null
     */
    public TaxResult taxForLine(Customer customer, String shipToCountry, String category, BigDecimal lineNet) {
        if (isReverseCharge(customer, shipToCountry)) {
            return new TaxResult(BigDecimal.ZERO, Money.ZERO, true);
        }
        BigDecimal rate = rateFor(shipToCountry, category);
        BigDecimal amount = roundTax(lineNet.multiply(rate));
        return new TaxResult(rate, amount, false);
    }

    /**
     * Tax for every line of a priced order. The category list is parallel to the results.
     */
    public List<TaxResult> taxForLines(Customer customer, String shipToCountry,
            List<String> categories, List<LineResult> lines) {
        List<TaxResult> out = new ArrayList<TaxResult>();
        for (int i = 0; i < lines.size(); i++) {
            String category = i < categories.size() ? categories.get(i) : null;
            out.add(taxForLine(customer, shipToCountry, category, lines.get(i).getNet()));
        }
        return out;
    }

    public BigDecimal sumTax(List<TaxResult> results) {
        BigDecimal total = Money.ZERO;
        for (TaxResult r : results) {
            total = total.add(r.getAmount());
        }
        return total;
    }

    public boolean isEuCountry(String code) {
        return code != null && euCountries.contains(code.trim().toUpperCase());
    }
}
