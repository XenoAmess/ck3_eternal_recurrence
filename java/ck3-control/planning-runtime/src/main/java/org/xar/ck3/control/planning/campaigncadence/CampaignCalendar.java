package org.xar.ck3.control.planning.campaigncadence;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;

/** Exact CK3 positive-year fixed-365 calendar; never Gregorian time. */
public final class CampaignCalendar {
    public static final String PROFILE = "ck3-1.20.0.4-cdate-fixed365-raw24/v1";
    public static final int RAW_EPOCH = 43_800_000;
    public static final int TICKS_PER_DAY = 24;
    private static final List<Integer> MONTH_LENGTHS = List.of(31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31);
    private static final LinkedHashMap<ScheduleKey, List<Boundary>> SCHEDULES = new LinkedHashMap<>(16, 0.75f, true);
    private record ScheduleKey(String startDate, int months) { }

    private CampaignCalendar() { }

    public record Date(int year, int month, int day) {
        public Date {
            require(year >= 1 && year <= 9999 && month >= 1 && month <= 12,
                    "date outside positive-year CK3 profile");
            require(day >= 1 && day <= MONTH_LENGTHS.get(month - 1), "invalid fixed-365 CK3 day");
        }

        public String text() { return year + "." + month + "." + day; }

        public int raw() {
            int days = year * 365 + day - 1;
            for (int index = 0; index < month - 1; index++) { days += MONTH_LENGTHS.get(index); }
            return RAW_EPOCH + TICKS_PER_DAY * days;
        }
    }

    public record Boundary(String date, int raw) {
        public Boundary { require(parse(date).raw() == raw, "date/raw boundary mismatch"); }
    }

    public static Date parse(String date) {
        require(date != null && date.matches("[0-9]+\\.[0-9]+\\.[0-9]+") && date.length() <= 32,
                "CK3 date must be ASCII year.month.day");
        String[] parts = date.split("\\.");
        try {
            return new Date(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]));
        } catch (NumberFormatException error) {
            throw new IllegalArgumentException("CK3 date component outside integer domain", error);
        }
    }

    public static int dateToRaw(String date) { return parse(date).raw(); }

    public static String rawToDate(int raw) {
        require(Math.floorMod(raw - (long) RAW_EPOCH, TICKS_PER_DAY) == 0, "whole native CK3 day required");
        long days = (raw - (long) RAW_EPOCH) / TICKS_PER_DAY;
        int year = Math.toIntExact(Math.floorDiv(days, 365));
        int dayIndex = Math.floorMod(days, 365);
        require(year >= 1 && year <= 9999, "CK3 year outside positive-year cadence profile");
        int month = 1;
        for (int length : MONTH_LENGTHS) {
            if (dayIndex < length) { return new Date(year, month, dayIndex + 1).text(); }
            month++;
            dayIndex -= length;
        }
        throw new IllegalArgumentException("invalid native day index");
    }

    public static synchronized List<Boundary> monthBoundaries(String startDate, int months) {
        Date start = parse(startDate);
        require(months >= 1 && months <= 360, "cadence requires 1..360 months");
        ScheduleKey key = new ScheduleKey(startDate, months);
        List<Boundary> cached = SCHEDULES.get(key);
        if (cached != null) { return cached; }
        List<Boundary> rows = new ArrayList<>(months + 1);
        for (int index = 0; index <= months; index++) {
            int monthIndex = start.year() * 12 + start.month() - 1 + index;
            int year = monthIndex / 12;
            int month = monthIndex % 12 + 1;
            Date date = new Date(year, month, Math.min(start.day(), MONTH_LENGTHS.get(month - 1)));
            rows.add(new Boundary(date.text(), date.raw()));
        }
        List<Boundary> result = List.copyOf(rows);
        if (SCHEDULES.size() >= 16) { SCHEDULES.pollFirstEntry(); }
        SCHEDULES.put(key, result);
        return result;
    }
}
