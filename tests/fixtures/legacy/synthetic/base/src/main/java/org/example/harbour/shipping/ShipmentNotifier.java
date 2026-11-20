package org.example.harbour.shipping;

import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.example.harbour.util.Config;

/**
 * Sends shipment notices to the carrier interface.
 */
public class ShipmentNotifier {

    private static final Logger LOG = Logger.getLogger(ShipmentNotifier.class.getName());

    private static final long[] RETRY_WAITS_MS = {1000L, 2000L, 4000L};

    private final ParkedNoticeStore parked;

    public ShipmentNotifier(ParkedNoticeStore parked) {
        this.parked = parked;
    }

    /**
     * Posts the notice. After the first failure it tries again three times and parks the notice if all fail.
     *
     * @return true when the carrier accepted the notice
     */
    public boolean sendWithRetry(ShipmentNotice notice) {
        String lastError = null;
        for (int attempt = 0; attempt <= RETRY_WAITS_MS.length; attempt++) {
            if (attempt > 0) {
                try {
                    Thread.sleep(RETRY_WAITS_MS[attempt - 1]);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    lastError = "interrupted";
                    break;
                }
            }
            try {
                int status = postNotice(notice);
                if (status >= 200 && status < 300) {
                    return true;
                }
                lastError = "HTTP " + status;
            } catch (IOException e) {
                lastError = e.toString();
            }
            LOG.warning("notice for order " + notice.getOrderId() + " failed (" + lastError + ")");
        }
        parked.park(notice, lastError);
        return false;
    }

    /**
     * One HTTP POST to the carrier, returns the status code.
     */
    int postNotice(ShipmentNotice notice) throws IOException {
        URL url = new URL(Config.get("carrier.notice.url", "http://localhost:8080/carrier/notices"));
        HttpURLConnection con = (HttpURLConnection) url.openConnection();
        try {
            con.setRequestMethod("POST");
            con.setConnectTimeout(5000);
            con.setReadTimeout(10000);
            con.setDoOutput(true);
            con.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            byte[] body = notice.toJson().getBytes(StandardCharsets.UTF_8);
            OutputStream out = con.getOutputStream();
            try {
                out.write(body);
            } finally {
                out.close();
            }
            return con.getResponseCode();
        } finally {
            con.disconnect();
        }
    }

    /**
     * Fire and forget variant used by the nightly batch. Errors only go to the log.
     */
    public void sendQuietly(ShipmentNotice notice) {
        try {
            sendWithRetry(notice);
        } catch (Exception e) {
            LOG.log(Level.SEVERE, "notice sender crashed", e);
        }
    }
}
