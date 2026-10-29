package org.xar.ck3.control.wave2.military.wardeclaredoverview;

import java.util.Optional;
import org.xar.ck3.control.wave2.military.warresults.WarResultsCodec;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Observation;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Plan;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.QueryFrame;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Request;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.Snapshot;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowPresence;

/** In-process declared-overview facade over the single typed window-priority engine. */
public final class WarDeclaredOverviewPolicy {
    public static final String SCHEMA = "xar.ck3.war-declared-overview-priority-input/v1";
    private static final WindowKind KIND = WindowKind.DECLARED_OVERVIEW;

    private WarDeclaredOverviewPolicy() { }

    public static Request decode(byte[] input) { return WarResultsCodec.decode(input, KIND); }
    public static byte[] encodeRequest(Request request) { return WarResultsCodec.encodeRequest(request, KIND); }
    public static Optional<Plan> plan(Request request) { return WarResultsPolicy.plan(request, KIND); }
    public static byte[] encodePlan(Optional<Plan> plan) { return WarResultsCodec.encodePlan(plan, KIND); }
    public static WindowPresence presence(Observation observation) { return WarResultsPolicy.presence(observation); }
    public static QueryFrame queryFrame(Snapshot snapshot) { return WarResultsPolicy.queryFrame(snapshot); }
    public static byte[] encodeQueryFrame(QueryFrame frame) { return WarResultsCodec.encodeQueryFrame(frame); }
}
