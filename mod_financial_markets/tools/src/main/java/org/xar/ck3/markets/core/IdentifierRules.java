package org.xar.ck3.markets.core;

final class IdentifierRules {
    private IdentifierRules() {
    }

    static void validate(String value, String label) {
        if (value == null || !value.matches("[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}")) {
            throw new IllegalArgumentException(label + " must be 1-96 stable ASCII identifier characters");
        }
    }
}
