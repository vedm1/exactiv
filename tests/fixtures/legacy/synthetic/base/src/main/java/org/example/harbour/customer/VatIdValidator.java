package org.example.harbour.customer;

import java.util.regex.Pattern;

/**
 * Checks the shape of a VAT id. It does not ask any registry whether the id exists.
 */
public final class VatIdValidator {

    private static final Pattern DE_FORM = Pattern.compile("^DE[0-9]{9}$");
    private static final Pattern FR_FORM = Pattern.compile("^FR[A-Z0-9]{2}[0-9]{9}$");

    private VatIdValidator() {
    }

    public static boolean isValidVatId(String vatId) {
        if (vatId == null) {
            return false;
        }
        String id = vatId.trim().toUpperCase();
        if (id.startsWith("DE")) {
            return id.length() == 11 && DE_FORM.matcher(id).matches();
        }
        if (id.startsWith("FR")) {
            return id.length() == 13 && FR_FORM.matcher(id).matches();
        }
        return false;
    }

    /**
     * Country prefix of an id, or null when the id is blank.
     */
    public static String prefixOf(String vatId) {
        if (vatId == null || vatId.trim().length() < 2) {
            return null;
        }
        return vatId.trim().substring(0, 2).toUpperCase();
    }
}
