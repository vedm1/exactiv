package org.example.harbour.invoice;

import java.util.regex.Pattern;
import java.util.logging.Logger;

import org.example.harbour.util.Strings;

/**
 * Hands out invoice numbers like INV-2026-000123.
 */
public class InvoiceNumberGenerator {

    private static final Logger LOG = Logger.getLogger(InvoiceNumberGenerator.class.getName());

    private static final Pattern NUMBER_PATTERN = Pattern.compile("INV-\\d{4}-\\d{6}");

    private final InvoiceDao dao;

    public InvoiceNumberGenerator(InvoiceDao dao) {
        this.dao = dao;
    }

    public synchronized String nextNumber(int year) {
        String candidate;
        do {
            long seq = dao.nextSequence(year);
            candidate = "INV-" + year + "-" + Strings.padLeft(String.valueOf(seq), 6, '0');
            if (!NUMBER_PATTERN.matcher(candidate).matches()) {
                throw new InvoiceException("generated number has bad format: " + candidate);
            }
        } while (dao.numberExists(candidate));
        LOG.fine("new invoice number " + candidate);
        return candidate;
    }

    public boolean looksValid(String number) {
        return number != null && NUMBER_PATTERN.matcher(number).matches();
    }
}
