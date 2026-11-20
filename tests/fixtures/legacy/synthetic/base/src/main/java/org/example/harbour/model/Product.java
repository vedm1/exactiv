package org.example.harbour.model;

import java.math.BigDecimal;

/**
 * A catalogue item.
 */
public class Product implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private String sku;
    private String name;
    private String category;
    private BigDecimal unitPrice;
    private BigDecimal weightKg = BigDecimal.ONE;
    private int lengthCm = 10;
    private int widthCm = 10;
    private int heightCm = 10;
    private boolean hazardous = false;
    private boolean backorderable = false;

    public String getSku() { return sku; }

    public void setSku(String sku) { this.sku = sku; }

    public String getName() { return name; }

    public void setName(String name) { this.name = name; }

    public String getCategory() { return category; }

    public void setCategory(String category) { this.category = category; }

    public BigDecimal getUnitPrice() { return unitPrice; }

    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }

    public BigDecimal getWeightKg() { return weightKg; }

    public void setWeightKg(BigDecimal weightKg) { this.weightKg = weightKg; }

    public int getLengthCm() { return lengthCm; }

    public void setLengthCm(int lengthCm) { this.lengthCm = lengthCm; }

    public int getWidthCm() { return widthCm; }

    public void setWidthCm(int widthCm) { this.widthCm = widthCm; }

    public int getHeightCm() { return heightCm; }

    public void setHeightCm(int heightCm) { this.heightCm = heightCm; }

    public boolean isHazardous() { return hazardous; }

    public void setHazardous(boolean hazardous) { this.hazardous = hazardous; }

    public boolean isBackorderable() { return backorderable; }

    public void setBackorderable(boolean backorderable) { this.backorderable = backorderable; }

}
