package org.example.harbour.audit;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;

/**
 * JDBC access to the audit table.
 */
public class AuditDao {

    private final Connection con;

    public AuditDao(Connection con) {
        this.con = con;
    }

    public long insert(AuditEntry e) throws SQLException {
        PreparedStatement ps = con.prepareStatement(
                "INSERT INTO audit_log (user_name, subject, old_value, new_value, at) VALUES (?, ?, ?, ?, ?)",
                Statement.RETURN_GENERATED_KEYS);
        ResultSet keys = null;
        try {
            ps.setString(1, e.getUserName());
            ps.setString(2, e.getSubject());
            ps.setString(3, e.getOldValue());
            ps.setString(4, e.getNewValue());
            ps.setTimestamp(5, Timestamp.valueOf(e.getAt()));
            ps.executeUpdate();
            keys = ps.getGeneratedKeys();
            keys.next();
            long id = keys.getLong(1);
            e.setId(id);
            return id;
        } finally {
            if (keys != null) {
                keys.close();
            }
            ps.close();
        }
    }

    public List<AuditEntry> findBySubject(String subjectPrefix) throws SQLException {
        List<AuditEntry> out = new ArrayList<AuditEntry>();
        PreparedStatement ps = con.prepareStatement(
                "SELECT id, user_name, subject, old_value, new_value, at FROM audit_log "
                + "WHERE subject LIKE ? ORDER BY id");
        ResultSet rs = null;
        try {
            ps.setString(1, subjectPrefix + "%");
            rs = ps.executeQuery();
            while (rs.next()) {
                AuditEntry e = new AuditEntry(rs.getString("user_name"), rs.getString("subject"),
                        rs.getString("old_value"), rs.getString("new_value"),
                        rs.getTimestamp("at").toLocalDateTime());
                e.setId(rs.getLong("id"));
                out.add(e);
            }
        } finally {
            if (rs != null) {
                rs.close();
            }
            ps.close();
        }
        return out;
    }

    public int countAll() throws SQLException {
        Statement st = con.createStatement();
        try {
            ResultSet rs = st.executeQuery("SELECT COUNT(*) FROM audit_log");
            rs.next();
            return rs.getInt(1);
        } finally {
            st.close();
        }
    }
}
