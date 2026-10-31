package org.xar.ck3.research.m3;

import java.util.List;

/** Owner source-derived literals after two rejected model books; target source was reviewed. */
public final class CapacityIndexCases179 {
    private CapacityIndexCases179() { }
    public static List<CapacityIndexApi179.Input> cases() {
        return List.of(
            new CapacityIndexApi179.Input("negative-min-bias", Integer.MIN_VALUE, 9, 9),
            new CapacityIndexApi179.Input("zero-negative-bias", 0, -7, 3),
            new CapacityIndexApi179.Input("one-max-bias", 1, Integer.MAX_VALUE, Integer.MAX_VALUE),
            new CapacityIndexApi179.Input("two-positive-bias", 2, 4, 5),
            new CapacityIndexApi179.Input("eight", 8, 0, 3),
            new CapacityIndexApi179.Input("nine", 9, 0, 4),
            new CapacityIndexApi179.Input("sixteen", 16, 0, 4),
            new CapacityIndexApi179.Input("seventeen", 17, 0, 5),
            new CapacityIndexApi179.Input("max-count", Integer.MAX_VALUE, 0, 31),
            new CapacityIndexApi179.Input("negative-bias", 17, -7, 3),
            new CapacityIndexApi179.Input("positive-add-wrap", Integer.MAX_VALUE, Integer.MAX_VALUE, 3),
            new CapacityIndexApi179.Input("min-bias-signed-clamp", Integer.MAX_VALUE, Integer.MIN_VALUE, 3)
        );
    }
}
