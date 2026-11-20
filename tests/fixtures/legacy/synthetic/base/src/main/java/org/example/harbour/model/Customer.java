package org.example.harbour.model;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * A buying customer.
 */
public class Customer implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private long id;
    private String name;
    private String email;
    private String countryCode;
    private String vatId;
    private CustomerTier tier = CustomerTier.STANDARD;
    private CustomerState state = CustomerState.ACTIVE;
    private int paymentTermsDays = 30;
    private BigDecimal creditLimit = BigDecimal.ZERO;
    private BigDecimal creditBalance = BigDecimal.ZERO;
    private LocalDate createdOn;
    private boolean partner = false;
    private int groupCode = 0;
    private String iban;

    public long getId() { return id; }

    public void setId(long id) { this.id = id; }

    public String getName() { return name; }

    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }

    public void setEmail(String email) { this.email = email; }

    public String getCountryCode() { return countryCode; }

    public void setCountryCode(String countryCode) { this.countryCode = countryCode; }

    public String getVatId() { return vatId; }

    public void setVatId(String vatId) { this.vatId = vatId; }

    public CustomerTier getTier() { return tier; }

    public void setTier(CustomerTier tier) { this.tier = tier; }

    public CustomerState getState() { return state; }

    public void setState(CustomerState state) { this.state = state; }

    public int getPaymentTermsDays() { return paymentTermsDays; }

    public void setPaymentTermsDays(int paymentTermsDays) { this.paymentTermsDays = paymentTermsDays; }

    public BigDecimal getCreditLimit() { return creditLimit; }

    public void setCreditLimit(BigDecimal creditLimit) { this.creditLimit = creditLimit; }

    public BigDecimal getCreditBalance() { return creditBalance; }

    public void setCreditBalance(BigDecimal creditBalance) { this.creditBalance = creditBalance; }

    public LocalDate getCreatedOn() { return createdOn; }

    public void setCreatedOn(LocalDate createdOn) { this.createdOn = createdOn; }

    public boolean isPartner() { return partner; }

    public void setPartner(boolean partner) { this.partner = partner; }

    public int getGroupCode() { return groupCode; }

    public void setGroupCode(int groupCode) { this.groupCode = groupCode; }

    public String getIban() { return iban; }

    public void setIban(String iban) { this.iban = iban; }

}
