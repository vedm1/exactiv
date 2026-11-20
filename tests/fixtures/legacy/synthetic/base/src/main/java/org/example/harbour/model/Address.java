package org.example.harbour.model;

/**
 * Postal address.
 */
public class Address implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private String street;
    private String city;
    private String postalCode;
    private String countryCode;

    public String getStreet() { return street; }

    public void setStreet(String street) { this.street = street; }

    public String getCity() { return city; }

    public void setCity(String city) { this.city = city; }

    public String getPostalCode() { return postalCode; }

    public void setPostalCode(String postalCode) { this.postalCode = postalCode; }

    public String getCountryCode() { return countryCode; }

    public void setCountryCode(String countryCode) { this.countryCode = countryCode; }

}
