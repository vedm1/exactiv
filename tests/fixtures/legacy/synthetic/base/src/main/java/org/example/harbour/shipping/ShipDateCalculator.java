package org.example.harbour.shipping;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;

import org.example.harbour.util.Dates;

/**
 * Plans the day on which the warehouse hands the parcel to the carrier.
 */
public class ShipDateCalculator {

    private static final LocalTime CUTOFF = LocalTime.of(14, 0);

    // The warehouse cut-off is 16:00 on weekdays.
    // Orders confirmed up to 16:00 ship the same business day,
    // everything later ships the day after the next business day.
    // Friday orders after the cut-off go out on Tuesday.
    public LocalDate plannedShipDate(LocalDateTime confirmedAt) {
        LocalDate day = confirmedAt.toLocalDate();
        if (confirmedAt.toLocalTime().isAfter(CUTOFF)) {
            return Dates.nextBusinessDay(day);
        }
        if (Dates.isWeekend(day)) {
            return Dates.nextBusinessDay(day);
        }
        return day;
    }

    /**
     * Days between confirmation and the planned ship date, for the status page.
     */
    public long waitingDays(LocalDateTime confirmedAt) {
        return Dates.daysBetween(confirmedAt.toLocalDate(), plannedShipDate(confirmedAt));
    }
}
