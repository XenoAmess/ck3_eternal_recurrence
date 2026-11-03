package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure admission against the actual canonical action chain; no separate nonce registry exists. */
public final class ProtocolIdentityAdmission {
    private ProtocolIdentityAdmission() { }
    public static void requireUnique(List<ActionReceipt> canonical, ActionCommand proposed) {
        Objects.requireNonNull(proposed); String id = RequestIds.forCommand(proposed);
        String body = ActionCodec.bodySha256(proposed);
        for (ActionReceipt previous : List.copyOf(canonical)) {
            ActionCommand original = previous.command();
            if (!original.origin().machineId().equals(proposed.origin().machineId())
                    || !original.origin().game().equals(proposed.origin().game())) continue;
            // Receipt construction checked the digest. Only this closed immutable body may retain it.
            // Public BigInteger subclasses can change their wire text after construction: keep their old path.
            boolean immutable = original.protocolIdentity() instanceof ProtocolRequestIdentity.BodyDerived
                    && original.origin() instanceof CommandOrigin.Gameplay
                    && original.expectation() instanceof CommandExpectation.Gameplay;
            if (immutable) {
                for (var observed : List.of(original.before(), original.expected().before())) {
                    var frame = observed.frame();
                    var birth = observed.game().creationFiletime().value();
                    immutable &= birth != null && birth.getClass() == java.math.BigInteger.class
                            && frame.identity().player() != null && frame.identity().player().getClass() == java.math.BigInteger.class
                            && frame.identity().nativeRevision() != null && frame.identity().nativeRevision().getClass() == java.math.BigInteger.class
                            && frame.identity().dateRaw() != null && frame.identity().dateRaw().getClass() == java.math.BigInteger.class
                            && frame.revision() != null && frame.revision().getClass() == java.math.BigInteger.class;
                }
                for (var values : List.of(original.claims().armyIds(), original.claims().allyCharacterIds(), original.claims().characterIds()))
                    for (var value : values)
                        immutable &= value != null && value.getClass() == java.math.BigInteger.class;
                for (var value : original.expected().values())
                    if (value instanceof org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger integer)
                        immutable &= integer.value() != null && integer.value().getClass() == java.math.BigInteger.class;
                var pending = new java.util.ArrayDeque<org.xar.ck3.control.planning.opportunity.OpportunityJson.Value>();
                pending.add(original.arguments());
                while (immutable && !pending.isEmpty()) {
                    var value = pending.removeLast();
                    if (value instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj object) {
                        for (var member : object.members().values()) {
                            if (member == null) { immutable = false; break; }
                            pending.add(member);
                        }
                    } else if (value instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr array) {
                        for (var member : array.items()) {
                            if (member == null) { immutable = false; break; }
                            pending.add(member);
                        }
                    } else if (value instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue integer) {
                        immutable = integer.value() != null && integer.value().getClass() == java.math.BigInteger.class;
                    }
                }
            }
            String originalId = immutable ? RequestIds.forActionBody(previous.bodySha256()) : RequestIds.forCommand(original);
            if (originalId.equals(id))
                StrictJson.require(original.actionId().equals(proposed.actionId()) && previous.bodySha256().equals(body)
                        && java.util.Arrays.equals(ActionCodec.encodeCommand(original), ActionCodec.encodeCommand(proposed)),
                        "original native protocol request ID is already bound to another complete canonical command");
        }
    }
}
