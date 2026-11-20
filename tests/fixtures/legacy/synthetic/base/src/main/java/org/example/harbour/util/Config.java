package org.example.harbour.util;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Reads harbour.properties from the class path. System properties win.
 */
public final class Config {

    private static final Properties PROPS = new Properties();

    static {
        InputStream in = Config.class.getResourceAsStream("/harbour.properties");
        if (in != null) {
            try {
                PROPS.load(in);
            } catch (IOException e) {
                // keep going with an empty set; callers use defaults
            } finally {
                try {
                    in.close();
                } catch (IOException ignore) {
                    // nothing to do
                }
            }
        }
    }

    private Config() {
    }

    public static String get(String key, String dflt) {
        String sys = System.getProperty(key);
        if (sys != null) {
            return sys;
        }
        return PROPS.getProperty(key, dflt);
    }

    public static int getInt(String key, int dflt) {
        String v = get(key, null);
        if (v == null) {
            return dflt;
        }
        try {
            return Integer.parseInt(v.trim());
        } catch (NumberFormatException e) {
            return dflt;
        }
    }

    public static boolean getBool(String key, boolean dflt) {
        String v = get(key, null);
        return v == null ? dflt : Boolean.valueOf(v.trim()).booleanValue();
    }
}
