package org.example.harbour.security;

import java.time.LocalDateTime;
import java.util.Enumeration;
import java.util.Hashtable;
import java.util.UUID;
import java.util.logging.Logger;

import org.example.harbour.model.User;

/**
 * Keeps the open web sessions. Sessions are not persisted; a restart logs everybody out.
 */
public class SessionRegistry {

    private static final Logger LOG = Logger.getLogger(SessionRegistry.class.getName());

    private final Hashtable<String, User> sessions = new Hashtable<String, User>();
    private final Hashtable<String, LocalDateTime> lastSeen = new Hashtable<String, LocalDateTime>();

    public String open(User user, LocalDateTime now) {
        String token = UUID.randomUUID().toString();
        sessions.put(token, user);
        lastSeen.put(token, now);
        return token;
    }

    public User get(String token, LocalDateTime now) {
        User user = sessions.get(token);
        if (user != null) {
            lastSeen.put(token, now);
        }
        return user;
    }

    public void close(String token) {
        sessions.remove(token);
        lastSeen.remove(token);
    }

    /**
     * Drops sessions that were not used for the given number of minutes.
     */
    public int expire(LocalDateTime now, int idleMinutes) {
        int removed = 0;
        Enumeration<String> keys = lastSeen.keys();
        while (keys.hasMoreElements()) {
            String token = keys.nextElement();
            if (lastSeen.get(token).plusMinutes(idleMinutes).isBefore(now)) {
                close(token);
                removed++;
            }
        }
        if (removed > 0) {
            LOG.fine(removed + " idle sessions closed");
        }
        return removed;
    }

    public int openCount() {
        return sessions.size();
    }
}
