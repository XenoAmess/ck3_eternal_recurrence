package org.xar.ck3.markets.core;

public record DayAdvanceResult(long previousDay, long currentDay, boolean advanced) {
}
