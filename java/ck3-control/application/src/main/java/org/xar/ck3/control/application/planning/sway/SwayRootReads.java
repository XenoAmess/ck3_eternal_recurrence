package org.xar.ck3.control.application.planning.sway;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;

/** The identical frozen Root families issue dynamic targets and original-action receipts. No prefix grants permission. */
public final class SwayRootReads implements SwayActionLifecycle.RegisteredReads {
    public record Target(long characterId) { public Target { SwayNativeWire.character(characterId); } }
    public record Receipt(long target, String actionId, BigInteger preCaptureEpoch) {
        public Receipt { SwayNativeWire.character(target); SwayNativeWire.action(actionId, false); SwayNativeWire.u64(preCaptureEpoch, 1); }
    }
    public record Sources(ExactRef definitions, ExactRef nativeDecoder, ExactRef observations) {
        public Sources { for (ExactRef source : List.of(definitions, nativeDecoder, observations)) StrictJson.require(source.bytes() > 0, "actual Sway read implementation/decoder source required"); }
    }
    private final RootReadContractCatalog.Family<Target, SwayNativeWire.TargetRead> targets;
    private final RootReadContractCatalog.Family<Receipt, SwayNativeWire.AppliedReceipt> receipts;
    private final java.util.EnumMap<SwayObservationReads.Kind, RootReadContractCatalog.Family<SwayObservationReads.Query, SwayObservationReads.Plane>> planes = new java.util.EnumMap<>(SwayObservationReads.Kind.class);
    private final java.util.EnumMap<SwayObservationReads.Kind, RootReadContractCatalog.Family<SwayObservationReads.JournalQuery, SwayObservationReads.JournalPlane>> journals = new java.util.EnumMap<>(SwayObservationReads.Kind.class);
    private final java.util.EnumMap<SwayObservationReads.Kind,RootReadContractCatalog.Family<SwayObservationReads.DirectQuery,SwayObservationReads.DirectPlane>> direct = new java.util.EnumMap<>(SwayObservationReads.Kind.class);
    private final RootReadContractCatalog.Family<SwayObservationReads.InvalidationQuery,SwayObservationReads.InvalidationPlane> invalidation;
    private RootReadContractCatalog catalog;
    /** Historical callers have no selected notification permission. Actual v2 runtime supplies its explicit flag. */
    public SwayRootReads(Sources sources) {this(sources,false);}
    public SwayRootReads(Sources sources,boolean invalidationReasonQuery) {
        Objects.requireNonNull(sources);
        invalidation=new RootReadContractCatalog.Family<>("sway-selected-notification-input-native-subject/v1",SwayObservationReads.InvalidationQuery.class,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.observations(),sources.observations(),value->{
                    var row=StrictJson.object();row.put("actor_character_id",value.subject().actorCharacterId());row.put("target_character_id",value.subject().targetCharacterId());row.put("scheme_instance_id",value.subject().schemeInstanceId());row.put("scheme_instance_generation",value.subject().schemeInstanceGeneration());row.put("after_sequence",value.afterSequence().toString());return raw(row);
                },value->new OperationKey(SwayObservationReads.INVALIDATION_STEP),value->SwayObservationReads.invalidationContract(sources.observations(),value,invalidationReasonQuery));
        targets = new RootReadContractCatalog.Family<>("sway-native-target-actual4/v1", Target.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), sources.definitions(), sources.nativeDecoder(),
                value -> { ObjectNode row = StrictJson.object(); row.put("target_character_id", value.characterId()); return raw(row); },
                value -> new OperationKey(SwayNativeWire.TARGET + value.characterId()), value -> SwayNativeBindings.target(sources.definitions(), value.characterId()));
        receipts = new RootReadContractCatalog.Family<>("sway-original-receipt-actual4/v1", Receipt.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), sources.definitions(), sources.nativeDecoder(),
                value -> { ObjectNode row = StrictJson.object(); row.put("target_character_id", value.target()); row.put("action_id", value.actionId()); row.put("pre_capture_epoch", value.preCaptureEpoch().toString()); return raw(row); },
                value -> new OperationKey(SwayNativeWire.RECEIPT + value.target()), value -> SwayNativeBindings.receipt(sources.definitions(), value.target(), value.actionId(), value.preCaptureEpoch()));
        for (SwayObservationReads.Kind kind : SwayObservationReads.Kind.values()) {
            planes.put(kind, new RootReadContractCatalog.Family<>("sway-" + kind.name().toLowerCase(java.util.Locale.ROOT) + "-actual4/v2", SwayObservationReads.Query.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), sources.observations(), sources.observations(),
                    value -> { StrictJson.require(value.kind()==kind,"observation family kind differs"); ObjectNode row=StrictJson.object();row.set("identity",SwayFormalCodec.identity(value.identity()));value.afterSequence().ifPresent(cursor->row.put("after_sequence",cursor.toString()));return raw(row); },
                    value -> new OperationKey(kind.step()), value -> SwayObservationReads.contract(sources.observations(), value)));
            if(kind==SwayObservationReads.Kind.COMPLETION||kind==SwayObservationReads.Kind.OPINION) {
                direct.put(kind,new RootReadContractCatalog.Family<>("sway-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-native-subject-actual4/v1",SwayObservationReads.DirectQuery.class,
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.observations(),sources.observations(),value->{
                            StrictJson.require(value.kind()==kind,"direct native family kind differs");var actors=value.subject().actors();var row=StrictJson.object();row.put("actor_character_id",actors.actorCharacterId());row.put("target_character_id",actors.targetCharacterId());
                            value.subject().instance().ifPresent(subject->{row.put("scheme_instance_id",subject.schemeInstanceId());row.put("scheme_instance_generation",subject.schemeInstanceGeneration());});return raw(row);
                        },value->new OperationKey(kind.step()),value->SwayObservationReads.directContract(sources.observations(),value)));
            }
            if(kind==SwayObservationReads.Kind.EXECUTION||kind==SwayObservationReads.Kind.TERMINATION) {
                journals.put(kind,new RootReadContractCatalog.Family<>("sway-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-native-subject-actual4/v1",SwayObservationReads.JournalQuery.class,
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.observations(),sources.observations(),value->{
                            StrictJson.require(value.kind()==kind,"native subject journal family kind differs");var row=StrictJson.object();
                            row.put("actor_character_id",value.subject().actorCharacterId());row.put("target_character_id",value.subject().targetCharacterId());
                            row.put("scheme_instance_id",value.subject().schemeInstanceId());row.put("scheme_instance_generation",value.subject().schemeInstanceGeneration());row.put("after_sequence",value.afterSequence().toString());return raw(row);
                        },value->new OperationKey(kind.step()),value->SwayObservationReads.journalContract(sources.observations(),value)));
            }
        }
    }
    /** Root must put these exact objects in its one catalog before attaching that catalog. */
    public List<RootReadContractCatalog.Family<?, ?>> families() {
        List<RootReadContractCatalog.Family<?, ?>> values = new ArrayList<>(); values.add(targets); values.add(receipts); values.addAll(planes.values());values.addAll(journals.values());values.addAll(direct.values());values.add(invalidation); return List.copyOf(values);
    }
    public synchronized void attach(RootReadContractCatalog actual) {
        Objects.requireNonNull(actual); StrictJson.require(catalog == null || catalog == actual, "Sway read catalog cannot be rebound");
        for (var family : families()) StrictJson.require(actual.families().stream().anyMatch(installed -> installed == family), "Sway family is not installed in the actual frozen Root catalog"); catalog = actual;
    }
    private synchronized RootReadContractCatalog catalog() { if (catalog == null) throw new IllegalStateException("actual Sway read family catalog is not attached"); return catalog; }
    @Override public ReadContract<SwayNativeWire.TargetRead> target(long target) { return catalog().issue(targets, new Target(target)); }
    @Override public ReadContract<SwayNativeWire.AppliedReceipt> receipt(long target, String actionId, BigInteger preCaptureEpoch) { return catalog().issue(receipts, new Receipt(target, actionId, preCaptureEpoch)); }
    @Override public ReadContract<SwayObservationReads.Plane> plane(SwayObservationReads.Kind kind, Identity identity) { return observation(SwayObservationReads.Query.current(kind,identity)); }
    public ReadContract<SwayObservationReads.Plane> observation(SwayObservationReads.Query query) {return catalog().issue(planes.get(Objects.requireNonNull(query).kind()),query);}
    public ReadContract<SwayObservationReads.JournalPlane> journal(SwayObservationReads.JournalQuery query) {return catalog().issue(journals.get(Objects.requireNonNull(query).kind()),query);}
    public ReadContract<SwayObservationReads.DirectPlane> direct(SwayObservationReads.DirectQuery query){return catalog().issue(direct.get(Objects.requireNonNull(query).kind()),query);}
    public ReadContract<SwayObservationReads.InvalidationPlane> invalidation(SwayObservationReads.InvalidationQuery query){return catalog().issue(invalidation,Objects.requireNonNull(query));}
    private static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value)); }
}
