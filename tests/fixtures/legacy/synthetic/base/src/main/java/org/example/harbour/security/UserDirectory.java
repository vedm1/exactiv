package org.example.harbour.security;

import java.util.Enumeration;
import java.util.Hashtable;
import java.util.Set;

import org.example.harbour.model.Role;
import org.example.harbour.model.User;

/**
 * In-memory store of users, loaded at start-up. The real store is the user table;
 * this class caches it.
 */
public class UserDirectory {

    private final Hashtable<String, User> users = new Hashtable<String, User>();
    private final Hashtable<String, String> hashes = new Hashtable<String, String>();

    public void add(User user, String password) {
        users.put(user.getName(), user);
        hashes.put(user.getName(), LoginService.hash(password));
    }

    public User find(String name) {
        if (name == null) {
            return null;
        }
        return users.get(name);
    }

    public String hashOf(String name) {
        return hashes.get(name);
    }

    public int size() {
        return users.size();
    }

    /**
     * Names of all users that hold the given role.
     */
    public String namesWithRole(Role role) {
        StringBuffer sb = new StringBuffer();
        Enumeration<String> keys = users.keys();
        while (keys.hasMoreElements()) {
            String key = keys.nextElement();
            Set<Role> roles = users.get(key).getRoles();
            if (roles.contains(role)) {
                if (sb.length() > 0) {
                    sb.append(", ");
                }
                sb.append(key);
            }
        }
        return sb.toString();
    }
}
