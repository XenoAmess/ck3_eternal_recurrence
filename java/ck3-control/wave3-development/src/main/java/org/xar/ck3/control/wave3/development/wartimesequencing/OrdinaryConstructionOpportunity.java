package org.xar.ck3.control.wave3.development.wartimesequencing;

import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Opportunity;

/** Existing selected-step grammar only; this is never a route, contact, arrival or victory observation. */
public final class OrdinaryConstructionOpportunity {
    private static final String PREFIX = "advance-route-contact-horizon-v1-";
    private static final BigInteger MAX_ID = BigInteger.valueOf(Integer.MAX_VALUE);
    private OrdinaryConstructionOpportunity() { }

    public static boolean matches(Optional<String> step, Optional<String> phase, Opportunity opportunity) {
        return switch (opportunity) {
            case CONTINUE_SELECTED_WORK -> true;
            case ORDINARY_ADVANCE -> step.filter("life-advance"::equals).isPresent();
            case PREWAR_ARBITRATION -> step.filter(DeclarationContract::isNativeDeclarationStep).isPresent();
            case QUIET_ROUTE_ADVANCE -> phase.filter("native_war_route_contact_horizon_progress"::equals).isPresent()
                    && step.filter(OrdinaryConstructionOpportunity::isAdvanceRouteContactHorizon).isPresent();
        };
    }

    /** Narrow Java continuation of the original canonical public-CUnit horizon step parser. */
    public static boolean isAdvanceRouteContactHorizon(String step) {
        if (step == null || step.length() > 32768 || !step.startsWith(PREFIX)) return false;
        String payload = step.substring(PREFIX.length()); int to = payload.indexOf("-to-");
        if (to < 0) return false; String subjectText = payload.substring(0, to);
        String tail = payload.substring(to + 4); int hostile = tail.indexOf("-h-");
        if (hostile < 0) return false; String targetText = tail.substring(0, hostile);
        String counted = tail.substring(hostile + 3); int separator = counted.indexOf('-');
        if (separator < 0) return false; String countText = counted.substring(0, separator);
        if (!canonicalCunit(subjectText) || !targetText.matches("[0-9]+") || !countText.matches("\\p{Nd}+")) return false;
        BigInteger subject = new BigInteger(subjectText), target = new BigInteger(targetText), count = decimal(countText);
        if (subject.compareTo(MAX_ID) > 0 || target.signum() <= 0 || target.compareTo(MAX_ID) > 0
                || count.signum() <= 0 || count.compareTo(BigInteger.valueOf(64)) > 0) return false;
        String[] ids = counted.substring(separator + 1).split("-", -1);
        if (ids.length != count.intValueExact()) return false;
        BigInteger previous = BigInteger.valueOf(-1);
        for (String text : ids) {
            if (!canonicalCunit(text)) return false; BigInteger id = new BigInteger(text);
            if (id.compareTo(MAX_ID) > 0 || id.compareTo(previous) <= 0 || id.equals(subject)) return false;
            previous = id;
        }
        return true;
    }
    private static boolean canonicalCunit(String text) { return text.matches("0|[1-9][0-9]*"); }
    private static BigInteger decimal(String text) {
        StringBuilder ascii = new StringBuilder(text.length());
        text.codePoints().forEach(value -> ascii.append((char) ('0' + Character.digit(value, 10))));
        return new BigInteger(ascii.toString());
    }
}
