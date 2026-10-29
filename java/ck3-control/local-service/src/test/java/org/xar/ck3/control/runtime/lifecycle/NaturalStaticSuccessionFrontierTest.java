package org.xar.ck3.control.runtime.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact actual static-file evidence is DATA; these are software boundary tests, not Root/Game proof. */
final class NaturalStaticSuccessionFrontierTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186";
    private static final Instant OBSERVED=Instant.parse("2026-10-24T09:20:11.396849700Z");
    private static final String ROOT="D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/resume-current-20261024-r3/m3_research/batch41-limited14/";
    private static final ExactRef CAPTURE=new ExactRef(ROOT+"capture-code-b/capture.json",4481,"a7805db57a0177f5a3df39039179e6b52636a49ca18a56710139f73690117c29");
    private static final ExactRef CODE=new ExactRef(ROOT+"capture-code-b/window-001.raw",655,"8d2a0ea60167d185cc71213770a1ee612cd4c51413c6bdc9875f72ea821b6668");
    private static final ExactRef TABLE=new ExactRef(ROOT+"capture-meta-a/window-004.raw",128,"f94f352ad55037fb6df709e3bf56d1709420a9f47c5a66014e8bff44c367e2c5");

    @Test void actualHandlerRfAndTypedIdlerSlotCannotDecodeAsAnEngineOrRetainedNaturalCause() {
        var diagnostic=StrictJson.object().put("schema","xar.m3.unqualified-static-handler-frontier/v1")
                .put("machine_id",MACHINE).put("observed_at_utc",OBSERVED.toString())
                .put("handler_primary_rva","0x44BA8A0").put("slot_offset",104)
                .put("complete_rf_begin","0xAF1F30").put("complete_rf_end_exclusive","0xAF21BF")
                .put("direct_AF1880_call_found",false).put("typed_idler_primary_rva","0x44BC418")
                .put("typed_idler_slot_offset",24).put("typed_idler_slot_target_rva","0xB20270")
                .put("actual_root_primary_A0_qualified",false).put("natural_daily_cause_qualified",false);
        diagnostic.set("capture",CAPTURE.toJson());diagnostic.set("whole_code",CODE.toJson());diagnostic.set("typed_table",TABLE.toJson());
        byte[] original=StrictJson.canonical(diagnostic);
        assertThrows(IllegalArgumentException.class,()->NaturalEngineClockProof.decode(original));
        assertThrows(IllegalArgumentException.class,()->PendingNaturalCauseProof.decode(original));
    }

    @Test void shapeValidMetadataWithStaticOriginalsStillFailsTheActualHeldRootAndPacketBinding() {
        // Public codec construction validates only its wire domain. It is deliberately not a private issuer.
        var data=new NaturalEngineClockProof(MACHINE,OBSERVED,"a".repeat(64),ActionReceipt.Outcome.UNRESOLVED,false,
                CAPTURE,CODE,CAPTURE,TABLE,CODE,CAPTURE);
        var decoded=NaturalEngineClockProof.decode(NaturalEngineClockProof.encode(data));
        ExactRef actualRoot=new ExactRef("D:/software-fixture/original-preclock-root.json",1,"b".repeat(64));
        ExactRef actualPacket=new ExactRef("D:/software-fixture/original-current-native.json",2,"c".repeat(64));
        assertThrows(IllegalArgumentException.class,()->decoded.requireBoundTo(MACHINE,OBSERVED,"a".repeat(64),actualRoot,actualPacket));
        assertFalse(decoded.replayAuthorized());assertEquals(ActionReceipt.Outcome.UNRESOLVED,decoded.clockOutcome());
    }
}
