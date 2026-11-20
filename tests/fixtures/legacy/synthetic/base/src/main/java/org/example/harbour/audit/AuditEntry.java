package org.example.harbour.audit;

import java.time.LocalDateTime;

/**
 * One line of the audit trail.
 */
public class AuditEntry {

    private long id;
    private final String userName;
    private final String subject;
    private final String oldValue;
    private final String newValue;
    private final LocalDateTime at;

    public AuditEntry(String userName, String subject, String oldValue, String newValue, LocalDateTime at) {
        this.userName = userName;
        this.subject = subject;
        this.oldValue = oldValue;
        this.newValue = newValue;
        this.at = at;
    }

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public String getUserName() {
        return userName;
    }

    /**
     * What was changed, for example "price:SKU-100".
     */
    public String getSubject() {
        return subject;
    }

    public String getOldValue() {
        return oldValue;
    }

    public String getNewValue() {
        return newValue;
    }

    public LocalDateTime getAt() {
        return at;
    }

    @Override
    public String toString() {
        return at + " " + userName + " " + subject + " [" + oldValue + " -> " + newValue + "]";
    }
}
