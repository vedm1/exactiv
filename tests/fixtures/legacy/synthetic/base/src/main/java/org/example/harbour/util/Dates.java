package org.example.harbour.util;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

/**
 * Small date helpers shared by the services.
 */
public final class Dates {

    private Dates() {
    }

    public static long daysBetween(LocalDate from, LocalDate to) {
        return ChronoUnit.DAYS.between(from, to);
    }

    public static boolean isWeekend(LocalDate d) {
        DayOfWeek w = d.getDayOfWeek();
        return w == DayOfWeek.SATURDAY || w == DayOfWeek.SUNDAY;
    }

    public static LocalDate nextBusinessDay(LocalDate d) {
        LocalDate n = d.plusDays(1);
        while (isWeekend(n)) {
            n = n.plusDays(1);
        }
        return n;
    }
}
