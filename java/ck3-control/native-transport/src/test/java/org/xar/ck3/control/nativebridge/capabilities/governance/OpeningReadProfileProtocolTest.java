package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.governance.GovernanceBorrowedSession;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.Unavailable;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile.Kind;

/** Synthetic protocol DATA/negative cases only. No packet is claimed to originate from C++ or an application-main ticket. */
final class OpeningReadProfileProtocolTest {
    private static final String READER="a".repeat(64),ABI="b".repeat(64);
    private static final OpeningReadProfile PROFILE=new OpeningReadProfile(new OpeningReadProfile.SourcePins(READER,ABI));
    private static final OpeningReadProfile.Frame FRAME=new OpeningReadProfile.Frame(BigInteger.valueOf(3),BigInteger.valueOf(24000),BigInteger.valueOf(-2130706431));

    @Test void observedUnavailableRemainsNullDataAndCannotInstallALiveRead() {
        for(Kind kind:Kind.values()) {
            ObjectNode row=unavailable(kind);RawJson raw=raw(row);var data=PROFILE.decodeData(kind,raw,FRAME);
            assertFalse(data.available());assertTrue(data.frame().isEmpty());assertTrue(data.government().isEmpty());assertTrue(data.progress().isEmpty());
            assertArrayEquals(raw.bytes(),data.original().bytes());assertThrows(IllegalArgumentException.class,data::requireApplicationMainOrigin);
            ObjectNode bad=row.deepCopy();bad.putNull("unavailable_reason");reject(kind,bad);
            bad=row.deepCopy();bad.put("date_raw",0);reject(kind,bad);
            bad=row.deepCopy();((ObjectNode)bad.get("readiness")).put("same_frame_ready",true);reject(kind,bad);
            bad=row.deepCopy();bad.put("action_ready",true);reject(kind,bad);
        }
    }
    @Test void exactSchemaFieldsetBuildPinsAndBooleanRolesCannotDrift() {
        ObjectNode original=unavailable(Kind.SCOPE);
        for(String key:List.of("schema","government","origin","provenance","read_only")) {ObjectNode bad=original.deepCopy();bad.remove(key);reject(Kind.SCOPE,bad);}
        ObjectNode bad=original.deepCopy();bad.put("campaign_root_context",true);reject(Kind.SCOPE,bad);
        bad=original.deepCopy();bad.put("schema",Kind.CURRENT.schema());reject(Kind.SCOPE,bad);
        bad=original.deepCopy();bad.put("read_only",false);reject(Kind.SCOPE,bad);
        bad=original.deepCopy();bad.put("full_governance_ready",true);reject(Kind.SCOPE,bad);
        for(String field:List.of("profile_id","adapter_id","game_version","executable_sha256","reader_source_sha256","abi_manifest_sha256")) {
            bad=original.deepCopy();((ObjectNode)bad.get("provenance")).put(field,"unqualified-other-value");reject(Kind.SCOPE,bad);
        }
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.SourcePins(READER.toUpperCase(),ABI));
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.SourcePins("0",ABI));
    }
    @Test void completeGovernmentFlagsKeepNativeOrderAndDuplicatesAsDataOnly() {
        ObjectNode row=available(Kind.SCOPE);var government=row.putObject("government");government.put("key","feudal_government").put("native_flag_count",3);
        government.putArray("flags").add("government_is_feudal").add("second_flag").add("government_is_feudal");
        var data=PROFILE.decodeData(Kind.SCOPE,raw(row),FRAME);
        assertEquals(List.of("government_is_feudal","second_flag","government_is_feudal"),data.government().orElseThrow().flags());
        assertThrows(UnsupportedOperationException.class,()->data.government().orElseThrow().flags().add("caller"));
        assertThrows(IllegalArgumentException.class,data::requireApplicationMainOrigin);
        ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("government")).put("native_flag_count",2);reject(Kind.SCOPE,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("government")).put("native_flag_count",3.0);reject(Kind.SCOPE,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("government")).putArray("flags").add("government_is_feudal").add(0).add("second_flag");reject(Kind.SCOPE,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("origin")).put("main_owner_observed",true);reject(Kind.SCOPE,bad);
    }
    @Test void completeSignedActorAndUnsignedRevisionNeverNarrowIntoLegacyIdentities() {
        for(BigInteger actor:List.of(BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE))) {
            BigInteger rev=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
            var expected=new OpeningReadProfile.Frame(rev,BigInteger.valueOf(Integer.MIN_VALUE),actor);
            ObjectNode row=available(Kind.SCOPE);row.put("native_revision",rev).put("snapshot_id","native:"+rev).put("date_raw",Integer.MIN_VALUE).put("player_character_id",actor);
            var g=row.putObject("government");g.put("key","actual_software_definition").put("native_flag_count",0);g.putArray("flags");
            var data=PROFILE.decodeData(Kind.SCOPE,raw(row),expected);assertEquals(expected,data.frame().orElseThrow());
            assertThrows(IllegalArgumentException.class,()->PROFILE.decodeData(Kind.SCOPE,raw(row),FRAME));
        }
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.Frame(BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->new OpeningReadProfile.Frame(BigInteger.ONE,BigInteger.ZERO,BigInteger.valueOf(-1)));
        ObjectNode bad=available(Kind.SCOPE);bad.put("native_revision",3.0);reject(Kind.SCOPE,bad);
        bad=available(Kind.SCOPE);bad.put("snapshot_id","native:03");reject(Kind.SCOPE,bad);
    }
    @Test void focusPresenceCounterTypesRangesAndOriginDoNotInventCurrentEvidence() {
        ObjectNode row=current();var data=PROFILE.decodeData(Kind.CURRENT,raw(row),FRAME);
        assertEquals(BigInteger.valueOf(Long.MAX_VALUE),data.progress().orElseThrow().xpTotalRaw().orElseThrow());
        assertEquals(BigInteger.valueOf(20),data.progress().orElseThrow().xpWithinLevelRaw().orElseThrow());
        assertThrows(IllegalArgumentException.class,data::requireApplicationMainOrigin);
        for(String field:List.of("xp_total_raw","xp_within_level_raw","xp_per_level","unspent_perk_points","used_perk_points")) {
            ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put(field,-1);reject(Kind.CURRENT,bad);
            bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put(field,"1");reject(Kind.CURRENT,bad);
        }
        for(String field:List.of("xp_per_level","unspent_perk_points","used_perk_points")) {
            ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put(field,BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE));reject(Kind.CURRENT,bad);
        }
        ObjectNode bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("xp_total_raw",BigInteger.valueOf(Long.MAX_VALUE).add(BigInteger.ONE));reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("xp_within_level_raw",100000000);reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_focus")).put("presence","absent");
        for(String key:List.of("key","lifestyle_key"))((ObjectNode)bad.get("current_focus")).putNull(key);
        var absent=(ObjectNode)bad.get("current_lifestyle_progress");absent.put("presence","absent");
        for(String key:List.of("lifestyle_key","xp_total_raw","xp_within_level_raw","xp_per_level","unspent_perk_points","used_perk_points"))absent.putNull(key);
        reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("presence","absent");reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_focus")).put("presence","unknown");reject(Kind.CURRENT,bad);
        bad=row.deepCopy();((ObjectNode)bad.get("current_lifestyle_progress")).put("lifestyle_key","other_style");reject(Kind.CURRENT,bad);
        bad=row.deepCopy();var origin=(ObjectNode)bad.get("origin");origin.put("source_kind","application_main_ticket").put("main_owner_observed",true).put("ticket_sequence",0).put("pump_epoch",1).put("thread_id",1);reject(Kind.CURRENT,bad);
    }
    @Test void full111SoftwareRepliesUseTheExactOriginalSource56Frame() throws Exception {
        var frame = full111Frame();
        var profile = OpeningReadProfile.full111DataProfile();
        var scope = available(Kind.SCOPE);
        scope.putObject("government").put("key", "feudal_government").put("native_flag_count", 1)
                .putArray("flags").add("government_is_feudal");
        for (Kind kind : Kind.values()) {
            var row = full111(kind == Kind.SCOPE ? scope : current(), profile, kind);
            row.put("native_revision", frame.nativeRevision()).put("snapshot_id", frame.snapshotId())
                    .put("date_raw", frame.dateRaw()).put("player_character_id", frame.playerCharacterId());
            var data = profile.decodeData(kind, raw(row), frame);
            assertEquals(frame, data.frame().orElseThrow());
            assertArrayEquals(raw(row).bytes(), data.original().bytes());
            assertThrows(IllegalArgumentException.class, data::requireApplicationMainOrigin);
            assertThrows(IllegalArgumentException.class, () -> PROFILE.decodeData(kind, raw(row), frame));
            var crossed = new OpeningReadProfile.Frame(frame.nativeRevision().add(BigInteger.ONE), frame.dateRaw(), frame.playerCharacterId());
            assertThrows(IllegalArgumentException.class, () -> profile.decodeData(kind, raw(row), crossed));
            var badBuild = row.deepCopy();
            ((ObjectNode) badBuild.get("provenance")).put("adapter_id", "ck3-1.21.0.3-26785313-msvc-x64");
            assertThrows(IllegalArgumentException.class, () -> profile.decodeData(kind, raw(badBuild), frame));
            var wrongActor = row.deepCopy().put("player_character_id", frame.playerCharacterId().add(BigInteger.ONE));
            assertThrows(IllegalArgumentException.class, () -> profile.decodeData(kind, raw(wrongActor), frame));
        }
        var missing = full111(unavailable(Kind.CURRENT), profile, Kind.CURRENT).put("unavailable_reason", "no_focus");
        var rejected = profile.decodeData(Kind.CURRENT, raw(missing), frame);
        assertFalse(rejected.available());
        assertTrue(rejected.frame().isEmpty());
        assertTrue(rejected.progress().isEmpty());
        assertEquals("no_focus", rejected.unavailableReason().orElseThrow());
    }

    @Test void full111ContractsKeepTheNewOperationPairSeparateFromUnqualifiedNative131() {
        var source = new ExactRef(Path.of("software-fixture.dll").toAbsolutePath().toString(),
                12389376L, "060a22216f6d7642ce2ee392dc7ffffbd17f1bb8d2029cd79eb17e47599b23f4");
        var build = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
        assertTrue(OpeningReadProfile.selectQualified(build.version(), build.executableSha256(), source).isEmpty());
        assertTrue(OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION, OpeningReadProfile.EXECUTABLE, source).isEmpty());
        // Software contract assembly only. Real registration above requires a separately reviewed DLL identity.
        var bindings = new OpeningReadProfile.Bindings(OpeningReadProfile.full111DataProfile(), source);
        assertEquals(List.of("query-current-lifestyle-scope-26785313-v1", "query-current-lifestyle-state-26785313-v1"),
                bindings.all().stream().map(contract -> contract.operation().value()).toList());
        assertEquals(List.of("game.query.current-lifestyle-scope.26785313.v1", "game.query.current-lifestyle-state.26785313.v1"),
                bindings.all().stream().map(contract -> contract.requiredCapability().orElseThrow()).toList());
        assertTrue(bindings.all().stream().allMatch(contract -> contract.advertisedRequired() && contract.hasPureReplay()));
        assertFalse(OpeningReadProfile.isCurrentOperation(bindings.scope().operation()));
        assertTrue(OpeningReadProfile.isCurrentOperation(bindings.current().operation()));
        var original = new OpeningReadProfile.Bindings(PROFILE, source);
        assertTrue(OpeningReadProfile.isCurrentOperation(original.current().operation()));
        assertNotEquals(bindings.current().contractId(), original.current().contractId());
    }

    @Test void full111OpeningDoesNotBorrowOrQueryWhenEitherCapabilityIsAbsent() throws Exception {
        var profile = OpeningReadProfile.full111DataProfile();
        var ref = new ExactRef(Path.of("software-fixture.dll").toAbsolutePath().toString(), 1, READER);
        var bindings = new OpeningReadProfile.Bindings(profile, ref);
        var forbidden = (InvocationHandler)(proxy, method, args) -> {
            throw new AssertionError("an incomplete capability pair must not reach " + method.getName());
        };
        var reader = noCalls(PlanningReadPort.class, forbidden);
        var archive = noCalls(OutcomeArchive.class, forbidden);
        var same = noCalls(Session.class, forbidden);
        var scope = new GovernanceBorrowedSession(same,
                Path.of("software-fixture.lock").toAbsolutePath(), ignored -> {
                    throw new AssertionError("an incomplete capability pair cannot acquire a writer scope");
                });
        var now = Instant.parse("2026-11-26T18:00:00Z");
        var port = OpeningReadProfile.readPort(bindings, reader, archive, scope, Clock.fixed(now, ZoneOffset.UTC), ignored -> { });
        var frame = full111Frame();
        var joint = new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(frame.playerCharacterId(), frame.nativeRevision(), frame.dateRaw()),
                frame.snapshotId(), BigInteger.valueOf(13), "source56-archive-test");
        var owner = new ObservationIdentity("source56-archive-test",
                new GameGeneration(50372, new PythonOnlyUInt64(new BigInteger("134401544348311914"))),
                joint, 3);
        var snapshot = StrictJson.object().put("paused", true).put("map_ready", true).put("snapshot_id", frame.snapshotId())
                .put("revision", joint.revision()).put("native_revision", frame.nativeRevision())
                .put("date_raw", frame.dateRaw()).put("episode_run_id", joint.episodeRunId());
        snapshot.putObject("played_character").put("character_id", frame.playerCharacterId());
        snapshot.putArray("active_wars");
        snapshot.putArray("player_armies");
        var semantic = (OpportunityJson.Obj)
                OpportunityJson.parse(StrictJson.canonical(snapshot));
        for (var definition : bindings.all()) {
            var observation = new PlanningObservation(semantic, List.of(), Set.of(),
                    Set.of(definition.requiredCapability().orElseThrow()), Optional.empty(), List.of(),
                    Optional.empty(), Optional.empty(), true);
            var request = new PlanningRequest(owner,
                    new G2Source(owner.machineId(), now.toString(), "Full111 software fixture", ref),
                    "source56-archive-test", now.plusSeconds(15), observation);
            var result = assertInstanceOf(Unavailable.class,
                    port.openingReadOnly(request).orElseThrow());
            assertTrue(result.reason().contains("both read-only capabilities"));
        }
    }

    private static <T> T noCalls(Class<T> type, InvocationHandler handler) {
        return type.cast(Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[] {type}, handler));
    }

    private static ObjectNode full111(ObjectNode row, OpeningReadProfile profile, Kind kind) {
        var build = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
        row.put("schema", kind == Kind.SCOPE ? "xar.ck3.lifestyle-scope.26785313.v1" : "xar.ck3.lifestyle-current.26785313.v1");
        ((ObjectNode) row.get("provenance")).put("profile_id", profile.profileId(kind)).put("adapter_id", build.coreFullAdapterId())
                .put("game_version", build.version()).put("executable_sha256", build.executableSha256().toUpperCase(Locale.ROOT))
                .put("reader_source_sha256", profile.pins().readerSourceSha256()).put("abi_manifest_sha256", profile.pins().abiManifestSha256());
        return row;
    }

    private static OpeningReadProfile.Frame full111Frame() throws Exception {
        try (var resource = OpeningReadProfileProtocolTest.class.getResourceAsStream("/opening-full111/source56-native26-full.bin")) {
            assertNotNull(resource);
            byte[] original = resource.readAllBytes();
            assertEquals("3677442a5b5a49c6a710d95d7305411212c71de8e7c5ef9d0035cfd160e66613",
                    ActionCodec.sha256(original));
            var snapshot = assertInstanceOf(NativeWire.Snapshot.class,
                    NativeWire.decode(original));
            var state = StrictJson.parse(snapshot.state().value());
            var build = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
            assertTrue(build.matches(state.get("game_version").textValue(), state.get("executable_sha256").textValue()));
            assertEquals(build.coreFullAdapterId(), state.get("adapter_id").textValue());
            assertTrue(state.get("paused").booleanValue());
            assertTrue(state.get("map_ready").booleanValue());
            return new OpeningReadProfile.Frame(snapshot.revision(), state.get("date_raw").bigIntegerValue(),
                    state.path("played_character").get("character_id").bigIntegerValue());
        }
    }

    private static ObjectNode current() {
        ObjectNode row=available(Kind.CURRENT);row.putObject("current_focus").put("presence","present").put("key","observed_focus").put("lifestyle_key","observed_style");
        row.putObject("current_lifestyle_progress").put("presence","present").put("lifestyle_key","observed_style").put("xp_total_raw",Long.MAX_VALUE)
                .put("xp_within_level_raw",20).put("xp_per_level",1000).put("unspent_perk_points",1).put("used_perk_points",2);return row;
    }
    private static ObjectNode available(Kind kind) {
        ObjectNode row=unavailable(kind);row.put("status","available").putNull("unavailable_reason");row.put("native_revision",FRAME.nativeRevision()).put("snapshot_id",FRAME.snapshotId())
                .put("date_raw",FRAME.dateRaw()).put("player_character_id",FRAME.playerCharacterId());
        var ready=(ObjectNode)row.get("readiness");ready.fieldNames().forEachRemaining(k->ready.put(k,true));
        ((ObjectNode)row.get("origin")).put("source_kind","offline_fixture");return row;
    }
    private static ObjectNode unavailable(Kind kind) {
        ObjectNode row=StrictJson.object().put("schema",kind.schema()).put("status","unavailable").put("unavailable_reason","synthetic_protocol_data_not_cpp")
                .put("read_only",true).put("full_governance_ready",false).put("action_ready",false);
        for(String key:List.of("native_revision","snapshot_id","date_raw","player_character_id"))row.putNull(key);
        var ready=row.putObject("readiness");ready.put("same_frame_ready",false);
        if(kind==Kind.SCOPE){row.putNull("government");ready.put("government_key_ready",false).put("government_flags_ready",false);}
        else {row.putNull("current_focus");row.putNull("current_lifestyle_progress");ready.put("current_focus_ready",false).put("lifestyle_progress_ready",false);}
        var origin=row.putObject("origin");origin.put("source_kind","unavailable").putNull("ticket_sequence").putNull("pump_epoch").putNull("thread_id").put("main_owner_observed",false);
        row.putObject("provenance").put("profile_id",kind.profile()).put("adapter_id",OpeningReadProfile.ADAPTER).put("game_version",OpeningReadProfile.VERSION)
                .put("executable_sha256",OpeningReadProfile.EXECUTABLE).put("reader_source_sha256",READER).put("abi_manifest_sha256",ABI);return row;
    }
    private static RawJson raw(ObjectNode row){return new RawJson(StrictJson.canonical(row));}
    private static void reject(Kind kind,ObjectNode row){assertThrows(IllegalArgumentException.class,()->PROFILE.decodeData(kind,raw(row),FRAME));}
}
