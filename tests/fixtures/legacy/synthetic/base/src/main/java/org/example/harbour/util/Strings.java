package org.example.harbour.util;

/**
 * String helpers. Kept static for historical reasons.
 */
public final class Strings {

    private Strings() {
    }

    public static boolean isEmpty(String s) {
        return s == null || s.trim().length() == 0;
    }

    public static String pad(String s, int len, char c) {
        StringBuilder sb = new StringBuilder();
        if (s != null) {
            sb.append(s);
        }
        while (sb.length() < len) {
            sb.append(c);
        }
        return sb.toString();
    }

    public static String padLeft(String s, int len, char c) {
        StringBuilder sb = new StringBuilder();
        int missing = len - (s == null ? 0 : s.length());
        for (int i = 0; i < missing; i++) {
            sb.append(c);
        }
        if (s != null) {
            sb.append(s);
        }
        return sb.toString();
    }
}
