package org.example.harbour.reporting;

import java.math.BigDecimal;
import java.time.YearMonth;
import java.util.Iterator;
import java.util.Map;

import org.example.harbour.util.Strings;

/**
 * Turns report data into text. Old code, uses StringBuffer and Iterator on purpose.
 */
public class ReportFormatter {

    private static final char SEP = ';';

    public String toCsv(Map<YearMonth, BigDecimal> monthly) {
        StringBuffer sb = new StringBuffer();
        sb.append("month").append(SEP).append("net").append('\n');
        Iterator<YearMonth> it = monthly.keySet().iterator();
        while (it.hasNext()) {
            YearMonth m = it.next();
            sb.append(m.toString()).append(SEP).append(monthly.get(m).toPlainString()).append('\n');
        }
        return sb.toString();
    }

    public String toTable(Map<YearMonth, BigDecimal> monthly) {
        StringBuffer sb = new StringBuffer();
        sb.append(Strings.pad("Month", 10, ' ')).append(Strings.padLeft("Net", 14, ' ')).append('\n');
        sb.append(Strings.pad("", 24, '-')).append('\n');
        for (Map.Entry<YearMonth, BigDecimal> e : monthly.entrySet()) {
            sb.append(Strings.pad(e.getKey().toString(), 10, ' '));
            sb.append(Strings.padLeft(e.getValue().setScale(2, java.math.RoundingMode.HALF_EVEN).toPlainString(), 14, ' '));
            sb.append('\n');
        }
        return sb.toString();
    }

    public String title(String name, int year) {
        if (Strings.isEmpty(name)) {
            return "Report " + year;
        }
        return name.trim() + " " + year;
    }

    /**
     * Quotes a text field for the CSV export when it contains the separator.
     */
    public String field(String value) {
        if (value == null) {
            return "";
        }
        if (value.indexOf(SEP) >= 0 || value.indexOf('"') >= 0) {
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }
        return value;
    }
}
