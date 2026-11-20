package org.example.harbour.legacy;

import java.util.Hashtable;

import org.example.harbour.model.Address;

/**
 * Address block for printed invoices.
 */
public class LegacyAddressFormatter {

    private static final Hashtable COUNTRY_NAMES = new Hashtable();

    static {
        COUNTRY_NAMES.put("DE", "Germany");
        COUNTRY_NAMES.put("FR", "France");
        COUNTRY_NAMES.put("NL", "Netherlands");
        COUNTRY_NAMES.put("AT", "Austria");
        COUNTRY_NAMES.put("BE", "Belgium");
    }

    public static String block(String recipient, Address a) {
        StringBuffer sb = new StringBuffer();
        if (recipient != null && recipient.length() > 0) {
            sb.append(recipient).append('\n');
        }
        if (a == null) {
            return sb.toString();
        }
        if (a.getStreet() != null) {
            sb.append(a.getStreet()).append('\n');
        }
        if ("NL".equals(a.getCountryCode())) {
            sb.append(a.getPostalCode()).append("  ").append(a.getCity());
        } else {
            sb.append(a.getPostalCode()).append(' ').append(a.getCity());
        }
        String name = (String) COUNTRY_NAMES.get(a.getCountryCode());
        if (name != null && !"DE".equals(a.getCountryCode())) {
            sb.append('\n').append(name.toUpperCase());
        }
        return sb.toString();
    }

    public static String oneLine(Address a) {
        if (a == null) {
            return "";
        }
        return a.getStreet() + ", " + a.getPostalCode() + " " + a.getCity() + " (" + a.getCountryCode() + ")";
    }
}
