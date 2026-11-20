package org.example.harbour.customer;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

import org.example.harbour.model.Customer;
import org.example.harbour.model.CustomerState;
import org.example.harbour.model.CustomerTier;
import org.example.harbour.util.Strings;

/**
 * In-memory filters for the customer list screen.
 */
public class CustomerSearch {

    public List<Customer> byName(List<Customer> all, String fragment) {
        if (Strings.isEmpty(fragment)) {
            return new ArrayList<Customer>(all);
        }
        final String needle = fragment.trim().toLowerCase();
        return all.stream()
                .filter(c -> c.getName() != null && c.getName().toLowerCase().contains(needle))
                .collect(Collectors.toList());
    }

    public List<Customer> byTier(List<Customer> all, CustomerTier tier) {
        return all.stream().filter(c -> c.getTier() == tier).collect(Collectors.toList());
    }

    public List<Customer> blocked(List<Customer> all) {
        List<Customer> out = new ArrayList<Customer>();
        for (Customer c : all) {
            if (c.getState() == CustomerState.BLOCKED) {
                out.add(c);
            }
        }
        return out;
    }

    public List<Customer> sortedByName(List<Customer> all) {
        List<Customer> copy = new ArrayList<Customer>(all);
        Collections.sort(copy, new Comparator<Customer>() {
            @Override
            public int compare(Customer a, Customer b) {
                String x = a.getName() == null ? "" : a.getName();
                String y = b.getName() == null ? "" : b.getName();
                return x.compareToIgnoreCase(y);
            }
        });
        return copy;
    }

    public Customer byEmail(List<Customer> all, String normalizedEmail) {
        for (Customer c : all) {
            if (normalizedEmail.equals(c.getEmail())) {
                return c;
            }
        }
        return null;
    }
}
