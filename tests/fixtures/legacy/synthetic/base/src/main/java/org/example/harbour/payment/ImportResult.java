package org.example.harbour.payment;

import java.util.ArrayList;
import java.util.List;

import org.example.harbour.model.Payment;

/**
 * Outcome of a bank statement import: payments that found an invoice, and lines that did not.
 */
public class ImportResult {

    private final List<Payment> matched = new ArrayList<Payment>();
    private final List<String> suspense = new ArrayList<String>();

    public List<Payment> getMatched() {
        return matched;
    }

    public List<String> getSuspense() {
        return suspense;
    }

    public int lineCount() {
        return matched.size() + suspense.size();
    }

    @Override
    public String toString() {
        return "ImportResult[matched=" + matched.size() + ", suspense=" + suspense.size() + "]";
    }
}
