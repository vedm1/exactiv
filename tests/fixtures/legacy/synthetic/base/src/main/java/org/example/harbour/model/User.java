package org.example.harbour.model;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

/**
 * A system user.
 */
public class User implements java.io.Serializable {

    private static final long serialVersionUID = 1L;

    private String name;
    private Set<Role> roles = new HashSet<Role>();
    private int failedAttempts = 0;
    private LocalDateTime lockedUntil;

    public String getName() { return name; }

    public void setName(String name) { this.name = name; }

    public Set<Role> getRoles() { return roles; }

    public void setRoles(Set<Role> roles) { this.roles = roles; }

    public int getFailedAttempts() { return failedAttempts; }

    public void setFailedAttempts(int failedAttempts) { this.failedAttempts = failedAttempts; }

    public LocalDateTime getLockedUntil() { return lockedUntil; }

    public void setLockedUntil(LocalDateTime lockedUntil) { this.lockedUntil = lockedUntil; }

}
