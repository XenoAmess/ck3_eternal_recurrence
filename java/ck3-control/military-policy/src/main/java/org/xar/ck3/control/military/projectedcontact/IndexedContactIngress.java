package org.xar.ck3.control.military.projectedcontact;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Available;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRequired;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Request;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Selection;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Side;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Transition;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Context;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Current;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Invalidation;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Lookup;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Outcome;

/** Ordinary endpoint Contact consumption after the independent first-hop branch.
 * This class consumes the existing effective-history projection and never creates it.
 * It provides operands for existing query/model paths, never an action permit.
 */
public final class IndexedContactIngress {
    private IndexedContactIngress() { }

    public sealed interface Decision permits NeedsQuery, NoContact, ResumeExisting, NewEncounter {
        Selection selection();
        default boolean actualArrivalObserved() { return false; }
        default boolean futureContactAuthorized() { return false; }
        default boolean authorizesCommandReplay() { return false; }
    }

    public record NeedsQuery(QueryRequired selection, Outcome reason) implements Decision {
        public NeedsQuery {
            Objects.requireNonNull(selection, "query required"); Objects.requireNonNull(reason, "reason");
            require(reason != Outcome.AVAILABLE, "available cannot require query");
        }
    }
    public record NoContact(Available selection) implements Decision {
        public NoContact { requireTransition(selection, Transition.NONE); }
    }
    /** Existing Combat ID/index and stored side order remain in selection.projection(). */
    public record ResumeExisting(Available selection) implements Decision {
        public ResumeExisting { requireTransition(selection, Transition.JOIN_EXISTING); }
        public int selectedCombatId() { return selection.projection().selectedCurrentCombatId(); }
        public int selectedCombatArrayIndex() { return selection.projection().selectedCurrentCombatArrayIndex(); }
    }

    public sealed interface Geometry permits IncomingAttackerEntry, DefenderConstructorZero { }
    public record IncomingAttackerEntry(int attackerEntryProvinceId) implements Geometry {
        public IncomingAttackerEntry { require(attackerEntryProvinceId > 0, "positive attacker entry required"); }
    }
    /** Native enum raw0 is observed constructor selection; it says nothing about its loaded effects. */
    public record DefenderConstructorZero() implements Geometry { }

    public record NewEncounter(Available selection, Geometry geometry) implements Decision {
        public NewEncounter {
            requireTransition(selection, Transition.CREATE_NEW); Objects.requireNonNull(geometry, "geometry");
            Side side = selection.projection().subjectSide();
            require(side == Side.ATTACKER && geometry instanceof IncomingAttackerEntry entry
                    && entry.attackerEntryProvinceId() == selection.projection().incomingEntryProvinceId()
                    || side == Side.DEFENDER && geometry instanceof DefenderConstructorZero,
                    "geometry must follow the native initiator role");
        }
        public Integer attackerEntryProvinceId() {
            return geometry instanceof IncomingAttackerEntry entry ? entry.attackerEntryProvinceId() : null;
        }
        public Integer constructorAdjacencyKindRaw() {
            return geometry instanceof DefenderConstructorZero ? 0 : null;
        }
        public int contactIncomingEntryProvinceId() { return selection.projection().incomingEntryProvinceId(); }
    }

    /** One immutable index per qualified effective-history/frame, reused for all request occurrences. */
    public sealed interface Frame permits IndexedFrame, UnavailableFrame {
        Decision select(Context current, Request request);
        int sourceRowsVisited();
    }

    private record IndexedFrame(SourceBoundContactIndex index) implements Frame {
        private IndexedFrame { Objects.requireNonNull(index, "index"); }
        @Override public Decision select(Context current, Request request) { return consume(index.select(current, request)); }
        @Override public int sourceRowsVisited() { return index.sourceRowsVisited(); }
    }
    private record UnavailableFrame(Outcome outcome) implements Frame {
        private UnavailableFrame { require(outcome != Outcome.AVAILABLE, "unavailable outcome required"); }
        @Override public Decision select(Context current, Request request) {
            Objects.requireNonNull(current, "current context"); Objects.requireNonNull(request, "request");
            return new NeedsQuery(new QueryRequired(request.key()), outcome);
        }
        @Override public int sourceRowsVisited() { return 0; }
    }

    public static Frame prepare(Context origin, List<QueryRow> effectiveRows) {
        Objects.requireNonNull(origin, "origin context"); Objects.requireNonNull(effectiveRows, "effective rows");
        if (!(origin instanceof Current current)) { return new UnavailableFrame(Outcome.UNKNOWN_CONTEXT); }
        if (current.invalidation() != Invalidation.NONE) { return new UnavailableFrame(Outcome.INVALIDATED); }
        return new IndexedFrame(SourceBoundContactIndex.build(current, effectiveRows));
    }

    private static Decision consume(Lookup lookup) {
        if (lookup.selection() instanceof QueryRequired required) { return new NeedsQuery(required, lookup.outcome()); }
        Available available = (Available) lookup.selection();
        return switch (available.projection().transition()) {
            case NONE -> new NoContact(available);
            case JOIN_EXISTING -> new ResumeExisting(available);
            case CREATE_NEW -> new NewEncounter(available,
                    available.projection().subjectSide() == Side.ATTACKER
                            ? new IncomingAttackerEntry(available.projection().incomingEntryProvinceId())
                            : new DefenderConstructorZero());
        };
    }

    private static void requireTransition(Available selection, Transition transition) {
        Objects.requireNonNull(selection, "available selection");
        require(selection.projection().transition() == transition, "wrong Contact transition");
    }
    private static void require(boolean valid, String message) {
        if (!valid) { throw new IllegalArgumentException(message); }
    }
}
