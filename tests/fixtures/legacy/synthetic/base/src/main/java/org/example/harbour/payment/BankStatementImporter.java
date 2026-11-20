package org.example.harbour.payment;

import java.io.BufferedReader;
import java.io.IOException;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.Map;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.example.harbour.model.Invoice;
import org.example.harbour.model.Payment;

/**
 * Reads a bank statement export (one line per booking, fields separated by semicolon):
 * <pre>booking date;amount;reference text</pre>
 */
public class BankStatementImporter {

    private static final Logger LOG = Logger.getLogger(BankStatementImporter.class.getName());

    private static final Pattern NUMBER_IN_TEXT = Pattern.compile("INV-[0-9]{4}-[0-9]{6}");

    public ImportResult importStatement(BufferedReader reader, Map<String, Invoice> invoicesByNumber) throws IOException {
        ImportResult result = new ImportResult();
        String line;
        int lineNo = 0;
        while ((line = reader.readLine()) != null) {
            lineNo++;
            if (line.trim().length() == 0 || line.startsWith("booking")) {
                continue;
            }
            String[] f = line.split(";", 3);
            if (f.length < 3) {
                result.getSuspense().add(line);
                continue;
            }
            try {
                LocalDate on = LocalDate.parse(f[0].trim());
                BigDecimal amount = new BigDecimal(f[1].trim().replace(',', '.'));
                Matcher m = NUMBER_IN_TEXT.matcher(f[2]);
                if (m.find() && invoicesByNumber.containsKey(m.group())) {
                    Payment p = new Payment();
                    p.setInvoiceNumber(m.group());
                    p.setAmount(amount);
                    p.setPaidOn(on);
                    result.getMatched().add(p);
                } else {
                    result.getSuspense().add(line);
                }
            } catch (DateTimeParseException e) {
                result.getSuspense().add(line);
            } catch (NumberFormatException e) {
                result.getSuspense().add(line);
            }
        }
        LOG.info("statement read: " + lineNo + " lines, " + result);
        return result;
    }

    /**
     * Quick look at the text before the import: how many lines mention an invoice number at all.
     */
    public int countReferences(String csv) {
        int n = 0;
        Matcher m = NUMBER_IN_TEXT.matcher(csv);
        while (m.find()) {
            n++;
        }
        return n;
    }
}
