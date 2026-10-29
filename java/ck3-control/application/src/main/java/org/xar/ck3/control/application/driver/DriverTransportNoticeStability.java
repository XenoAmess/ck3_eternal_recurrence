package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Source-defined Java wrappers only. Call after complete original manifest/native replay and independent Root source qualification.
 * Wrapper producer: the actual selected NativeDriverObservationProducer. Contracts 1/2 retain their historical
 * attribution; contract 3 uses the same typed heartbeat/pong wrappers and the shared seven-leaf native normalizer.
 * Its current exact producer/source closure must be qualified independently; accepting a version grants no source or readiness.
 * C++ bridge.cpp: 1611813B, SHA 41a3e271793e59cb87469324f0ef04611cc0277bedcc06d6fe1043c10fb83953;
 * heartbeat outer fields lines2567-2573, pong lines15439-15444. All other known and unknown fields remain exact.
 */
public final class DriverTransportNoticeStability {
    private static final BigInteger UINT64_MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private DriverTransportNoticeStability() { }
    public enum Kind {
        HEARTBEAT("last_heartbeat","heartbeat",Set.of("sequence","monotonic_ms")),
        PONG("last_pong","pong",Set.of("request_id"));
        private final String key,type;private final Set<String> wrappers;
        Kind(String key,String type,Set<String> wrappers){this.key=key;this.type=type;this.wrappers=wrappers;}
    }
    private record Notice(Kind kind,OpportunityJson.Obj payload) { }
    /** This projection supplies no capability or observation authority. Raw Native fields, including same-name diagnostic keys, stay strict. */
    public static OpportunityJson.Obj originalFields(DriverObservationFacts facts,NativeObservationPort.ObservedFrame actual) {
        StrictJson.require(facts.transport().equals(actual.session())&&facts.snapshotId().equals(actual.snapshotId())
                &&facts.nativeRevision().equals(actual.nativeRevision())&&facts.nativeStateSha256().equals(DriverJson.sha256(actual.state().bytes()))
                &&(facts.observationVersion()==1||facts.observationVersion()==2||facts.observationVersion()==3),"actual complete known-version Native producer required for notice projection");
        OpportunityJson.Obj fields=facts.originalSemanticFields();
        StrictJson.require(new OpportunityJson.Text("native-headless").equals(fields.get("backend_id"))
                &&new OpportunityJson.Text("injected-dll-named-pipe").equals(fields.get("source")),"notice wrappers require the actual source-defined Java Native producer");
        // Version 3 reuses the sole original framed-packet/raw-state verifier. It never re-normalizes canonical DATA.
        // Historical contracts retain their original raw-state strategy and exact missing/null/native-owned semantics.
        OpportunityJson.Obj raw=facts.observationVersion()==3 ? DriverObservationAssembler.originalNativeState(actual)
                : DriverJson.object(actual.state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        var diagnostics=OpportunityJson.object(fields.get("diagnostics"),"actual original diagnostics");
        var stable=new LinkedHashMap<>(diagnostics.members());
        for(Kind kind:Kind.values()) {
            // Even an explicit native null is native-owned. Missing, null and empty remain distinct.
            if(raw.get("diagnostics") instanceof OpportunityJson.Obj nativeDiagnostics&&nativeDiagnostics.members().containsKey(kind.key))continue;
            if(!diagnostics.members().containsKey(kind.key))continue;
            Notice notice=notice(kind,diagnostics.get(kind.key),facts.transport().game().pid());
            var payload=new LinkedHashMap<>(notice.payload().members());for(String field:kind.wrappers)payload.remove(field);
            stable.put(kind.key,new OpportunityJson.Obj(payload));
        }
        return fields.with("diagnostics",new OpportunityJson.Obj(stable));
    }
    public static OpportunityJson.Obj manifest(OpportunityJson.Obj actualManifest,DriverObservationFacts facts,NativeObservationPort.ObservedFrame actual) {
        StrictJson.require(actualManifest.get("original_semantic_fields").equals(facts.originalSemanticFields()),"stable notice projection requires the replayed original manifest fields");
        var fields=new LinkedHashMap<>(actualManifest.members());Instant.parse(OpportunityJson.text(fields.remove("observed_at"),"observed_at"));
        fields.put("original_semantic_fields",originalFields(facts,actual));return new OpportunityJson.Obj(fields);
    }
    public static OpportunityJson.Obj semantic(DriverObservationAssembler.Complete complete,DriverObservationFacts facts,
            NativeObservationPort.ObservedFrame actual,OpportunityJson.Obj verifiedStableManifest) {
        StrictJson.require(complete.semantic().get("diagnostics").equals(facts.originalSemanticFields().get("diagnostics")),
                "semantic diagnostics differ from the exact original Java producer fields");
        var fields=new LinkedHashMap<>(complete.semantic().members());fields.put("diagnostics",originalFields(facts,actual).get("diagnostics"));
        fields.put("java_driver_facts_evidence",verifiedStableManifest);return new OpportunityJson.Obj(fields);
    }
    private static Notice notice(Kind kind,OpportunityJson.Value value,long actualPid) {
        var payload=OpportunityJson.object(value,"actual typed transport notice");
        StrictJson.require(new OpportunityJson.Text(kind.type).equals(payload.get("type"))
                &&BigInteger.ONE.equals(OpportunityJson.integer(payload.get("protocol_version"),"protocol_version"))
                &&BigInteger.valueOf(actualPid).equals(OpportunityJson.integer(payload.get("pid"),"pid")),"transport wrapper type/protocol/Game source differs");
        if(kind==Kind.HEARTBEAT)for(String field:kind.wrappers) {
            BigInteger integer=OpportunityJson.integer(payload.get(field),field);StrictJson.require(integer.signum()>=0&&integer.compareTo(UINT64_MAX)<=0,"actual uint64 heartbeat wrapper required");
        }
        else StrictJson.require(OpportunityJson.text(payload.get("request_id"),"request_id").matches("[A-Za-z0-9_.-]{1,128}"),"actual source-qualified pong request identity required");
        return new Notice(kind,payload);
    }
}
