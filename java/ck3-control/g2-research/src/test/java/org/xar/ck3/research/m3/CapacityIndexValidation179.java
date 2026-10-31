package org.xar.ck3.research.m3;

public final class CapacityIndexValidation179 {
    private CapacityIndexValidation179() { }
    public static void main(String[] args) {
        int checks = 0;
        for (CapacityIndexApi179.Input input : CapacityIndexCases179.cases()) {
            int actual = CapacityIndex179.select(input.count(), input.bias());
            if (actual != input.expected()) {
                throw new AssertionError(input.id() + " expected=" + input.expected() + " actual=" + actual);
            }
            ++checks;
        }
        System.out.println("cases=" + checks + " semantic_checks=" + checks + " Native=0 Game=0 old_green=0");
    }
}
