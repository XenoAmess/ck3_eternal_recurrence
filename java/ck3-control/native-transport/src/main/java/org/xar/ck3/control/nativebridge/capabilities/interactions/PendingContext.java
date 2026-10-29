package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** The full pending-interaction contract, with unavailable structured semantics kept unavailable. */
public record PendingContext(Frame frame, PendingId instance, Status status, String reason, Definition definition,
        Roles roles, Target target, Options options, Routing routing, Deadline deadline, Boolean autoAccept,
        Legality legality, Terms terms, Readiness readiness, List<SourcePin> sourcePins) {
    public PendingContext { sourcePins=List.copyOf(sourcePins); }
    public enum Status { AVAILABLE, UNAVAILABLE, INVALID }
    public record Definition(String key, long deterministicHash, int runtimeOrdinal) { }
    /** Optional native roles use the original -1 sentinel; they are never normalized to zero or null. */
    public record Roles(int actor, int recipient, int secondaryActor, int secondaryRecipient, int intermediary) { }
    public record Target(boolean present, int typeIndex, String raw16BytesHex, String typeKey, String identityStatus,
            String typedIdentity, String typedIdentityReason) { }
    public record Option(int nativeIndex, int numericFlag, boolean selected, boolean shown, boolean valid,
            String canonicalStatus, String canonicalKey, String canonicalReason) { }
    public record Options(boolean exclusive, int count, List<Option> rows) { public Options { rows=List.copyOf(rows); } }
    public record Routing(int kind, int player, String responderRole, String replyChannel, boolean autoAcceptNotification) { }
    public record Deadline(int age, int expiration, int remaining, String boundary) { }
    public record Legal(boolean available, boolean allowed, String reason) { }
    public record Legality(Legal accept, Legal reject, Legal block, Legal acknowledge) { }
    public record War(String kind, String absoluteOutcome, int warId, String actorRole, String recipientRole) { }
    public record WarTerm(boolean available, War value, String reason) { }
    public record UnknownTerm(String reason) { }
    public record Ransom(boolean available, String reason, Integer actor, Integer jailer, Integer prisoner, Integer option,
            String optionKey, BigInteger goldRaw, Boolean shown, Boolean valid, Boolean hookSelected, Boolean ready,
            Optional<Boolean> ordinaryGoldReady) { }
    public record Terms(boolean specialDataPresent, WarTerm war, List<BigInteger> sentCosts, UnknownTerm exchanges,
            UnknownTerm effectPreview, UnknownTerm aiScore, UnknownTerm aiFinalDecision, Optional<Ransom> ransom) {
        public Terms { sentCosts=List.copyOf(sentCosts); }
    }
    public record Readiness(boolean definition, boolean roles, boolean targetKey, boolean targetIdentity, boolean options,
            boolean routing, boolean deadline, boolean autoAccept, boolean legality, boolean costs, boolean warBinding,
            boolean specialOutcome, boolean structuredTerms, boolean sameFrame, boolean semanticDecision, List<String> reasons) {
        public Readiness { reasons=List.copyOf(reasons); }
    }
    public record SourcePin(String name, String rvaOrIdentity) { }
}
