package org.example.harbour.shipping;

import java.io.Serializable;
import java.time.LocalDate;

import org.example.harbour.model.Carrier;

/**
 * What we tell the carrier about a parcel.
 */
public class ShipmentNotice implements Serializable {

    private static final long serialVersionUID = 1L;

    private long orderId;
    private Carrier carrier;
    private String recipient;
    private String postalCode;
    private String countryCode;
    private int parcels = 1;
    private LocalDate shipDate;

    public long getOrderId() {
        return orderId;
    }

    public void setOrderId(long orderId) {
        this.orderId = orderId;
    }

    public Carrier getCarrier() {
        return carrier;
    }

    public void setCarrier(Carrier carrier) {
        this.carrier = carrier;
    }

    public String getRecipient() {
        return recipient;
    }

    public void setRecipient(String recipient) {
        this.recipient = recipient;
    }

    public String getPostalCode() {
        return postalCode;
    }

    public void setPostalCode(String postalCode) {
        this.postalCode = postalCode;
    }

    public String getCountryCode() {
        return countryCode;
    }

    public void setCountryCode(String countryCode) {
        this.countryCode = countryCode;
    }

    public int getParcels() {
        return parcels;
    }

    public void setParcels(int parcels) {
        this.parcels = parcels;
    }

    public LocalDate getShipDate() {
        return shipDate;
    }

    public void setShipDate(LocalDate shipDate) {
        this.shipDate = shipDate;
    }

    /**
     * JSON body for the carrier interface. Built by hand, the interface is flat.
     */
    public String toJson() {
        StringBuffer sb = new StringBuffer();
        sb.append("{\"orderId\":").append(orderId);
        sb.append(",\"carrier\":\"").append(carrier).append('"');
        sb.append(",\"recipient\":\"").append(recipient == null ? "" : recipient.replace("\"", "'")).append('"');
        sb.append(",\"postalCode\":\"").append(postalCode).append('"');
        sb.append(",\"country\":\"").append(countryCode).append('"');
        sb.append(",\"parcels\":").append(parcels);
        sb.append(",\"shipDate\":\"").append(shipDate).append("\"}");
        return sb.toString();
    }
}
