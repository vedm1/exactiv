package org.example.harbour.audit;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;

/**
 * Small queries over a list of audit entries that was already loaded.
 */
public class AuditReport {

    public List<AuditEntry> forUser(List<AuditEntry> entries, String userName) {
        List<AuditEntry> out = new ArrayList<AuditEntry>();
        for (AuditEntry e : entries) {
            if (userName.equals(e.getUserName())) {
                out.add(e);
            }
        }
        return out;
    }

    public List<AuditEntry> onDay(List<AuditEntry> entries, LocalDate day) {
        List<AuditEntry> out = new ArrayList<AuditEntry>();
        for (AuditEntry e : entries) {
            if (e.getAt().toLocalDate().equals(day)) {
                out.add(e);
            }
        }
        return out;
    }

    /**
     * Number of entries per user name.
     */
    public Map<String, Integer> countByUser(List<AuditEntry> entries) {
        Hashtable<String, Integer> counts = new Hashtable<String, Integer>();
        for (AuditEntry e : entries) {
            Integer n = counts.get(e.getUserName());
            counts.put(e.getUserName(), n == null ? Integer.valueOf(1) : Integer.valueOf(n.intValue() + 1));
        }
        return counts;
    }

    public String render(List<AuditEntry> entries) {
        StringBuffer sb = new StringBuffer();
        for (AuditEntry e : entries) {
            sb.append(e.toString()).append("\n");
        }
        return sb.toString();
    }
}
