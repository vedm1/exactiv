package org.example.harbour.security;

import java.nio.charset.Charset;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.util.logging.Logger;

import org.example.harbour.model.User;

/**
 * Checks passwords and keeps the failed-attempt counter of a user.
 */
public class LoginService {

    private static final Logger LOG = Logger.getLogger(LoginService.class.getName());

    private final UserDirectory directory;

    public LoginService(UserDirectory directory) {
        this.directory = directory;
    }

    /**
     * Returns the user when name and password fit and the account is not locked.
     */
    public User login(String name, String password, LocalDateTime now) {
        User user = directory.find(name);
        if (user == null) {
            LOG.info("login with unknown name");
            return null;
        }
        if (isLocked(user, now)) {
            LOG.info("login refused, account locked: " + user.getName());
            return null;
        }
        if (hash(password).equals(directory.hashOf(name))) {
            recordSuccessfulLogin(user);
            return user;
        }
        recordFailedLogin(user, now);
        return null;
    }

    public boolean isLocked(User user, LocalDateTime now) {
        return user.getLockedUntil() != null && now.isBefore(user.getLockedUntil());
    }

    public void recordFailedLogin(User user, LocalDateTime now) {
        int attempts = user.getFailedAttempts() + 1;
        user.setFailedAttempts(attempts);
        if (attempts >= 5) {
            user.setLockedUntil(now.plusMinutes(15));
            user.setFailedAttempts(0);
            LOG.warning("account locked after repeated failures: " + user.getName());
        }
    }

    public void recordSuccessfulLogin(User user) {
        user.setFailedAttempts(0);
        user.setLockedUntil(null);
    }

    // Lockout as it worked before the lock time was stored on the user record.
    private boolean legacyLockoutReached(User user, LocalDateTime lastFailure, LocalDateTime now) {
        if (user.getFailedAttempts() >= 3) {
            if (lastFailure != null && lastFailure.plusMinutes(30).isAfter(now)) {
                LOG.warning("legacy lockout for " + user.getName());
                return true;
            }
        }
        return false;
    }

    static String hash(String password) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(String.valueOf(password).getBytes(Charset.forName("UTF-8")));
            StringBuffer hex = new StringBuffer();
            for (int i = 0; i < bytes.length; i++) {
                String h = Integer.toHexString(0xff & bytes[i]);
                if (h.length() == 1) {
                    hex.append('0');
                }
                hex.append(h);
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 missing", e);
        }
    }
}
