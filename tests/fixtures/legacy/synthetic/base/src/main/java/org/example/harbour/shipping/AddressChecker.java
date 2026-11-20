package org.example.harbour.shipping;

import java.util.regex.Pattern;

import org.example.harbour.model.Address;
import org.example.harbour.util.Strings;

/**
 * Format checks for ship-to addresses.
 */
public class AddressChecker {

    private static final Pattern FIVE_DIGITS = Pattern.compile("[0-9]{5}");
    private static final Pattern DUTCH = Pattern.compile("[0-9]{4}[A-Za-z]{2}");

    /**
     * Postal code format per country. Countries we do not ship to often are not checked.
     */
    public boolean isValidPostalCode(String countryCode, String postalCode) {
        if (countryCode == null || postalCode == null) {
            return false;
        }
        if (countryCode.equals("DE")) {
            return FIVE_DIGITS.matcher(postalCode).matches();
        }
        if (countryCode.equals("NL")) {
            return DUTCH.matcher(postalCode).matches();
        }
        if (countryCode.equals("FR")) {
            return FIVE_DIGITS.matcher(postalCode).matches();
        }
        return true;
    }

    /**
     * Full check of an address, returns null when fine or a message for the screen.
     */
    public String problemWith(Address a) {
        if (a == null) {
            return "no address";
        }
        if (Strings.isEmpty(a.getStreet()) || Strings.isEmpty(a.getCity())) {
            return "street and city are needed";
        }
        if (!isValidPostalCode(a.getCountryCode(), a.getPostalCode())) {
            return "postal code " + a.getPostalCode() + " does not fit country " + a.getCountryCode();
        }
        return null;
    }

    /**
     * Upper-cases and strips blanks before the check, the order screen sends what the user typed.
     */
    public String normalise(String postalCode) {
        if (postalCode == null) {
            return null;
        }
        return postalCode.replace(" ", "").toUpperCase();
    }
}
