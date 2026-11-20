package org.example.harbour.payment;

/**
 * Static IBAN checks. Written in 2009 style on purpose, do not "modernise" without tests.
 */
public final class IbanValidator {

    private IbanValidator() {
    }

    public static boolean isValidIban(String iban) {
        if (iban == null) {
            return false;
        }
        String s = iban.replace(" ", "").toUpperCase();
        if (s.length() < 5) {
            return false;
        }
        String country = s.substring(0, 2);
        int expected;
        if ("DE".equals(country)) {
            expected = 22;
        } else if ("NL".equals(country)) {
            expected = 18;
        } else if ("FR".equals(country)) {
            expected = 27;
        } else {
            return false;
        }
        if (s.length() != expected) {
            return false;
        }
        String moved = s.substring(4) + s.substring(0, 4);
        int remainder = 0;
        for (int i = 0; i < moved.length(); i++) {
            int value = Character.digit(moved.charAt(i), 36);
            if (value < 0) {
                return false;
            }
            String digits = Integer.toString(value);
            for (int k = 0; k < digits.length(); k++) {
                remainder = (remainder * 10 + (digits.charAt(k) - '0')) % 97;
            }
        }
        return remainder == 1;
    }

    /**
     * Groups an IBAN in blocks of four for printing.
     */
    public static String format(String iban) {
        if (iban == null) {
            return "";
        }
        String s = iban.replace(" ", "").toUpperCase();
        StringBuffer out = new StringBuffer();
        for (int i = 0; i < s.length(); i++) {
            if (i > 0 && i % 4 == 0) {
                out.append(' ');
            }
            out.append(s.charAt(i));
        }
        return out.toString();
    }

    public static String countryOf(String iban) {
        if (iban == null || iban.length() < 2) {
            return null;
        }
        return iban.substring(0, 2).toUpperCase();
    }
}
