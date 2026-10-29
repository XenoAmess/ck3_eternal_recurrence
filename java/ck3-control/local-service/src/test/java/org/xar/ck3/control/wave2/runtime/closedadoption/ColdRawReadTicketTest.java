package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket;
import static org.junit.jupiter.api.Assertions.*;

/** Actual strict release parser and production scope validator; no SDK worker or persistence file is opened. */
final class ColdRawReadTicketTest {
    private static final Path ROOT=Path.of("synthetic-read-ticket-scope").toAbsolutePath(),OWNED=ROOT.resolve("root-session");
    private static final Instant INJECTED=Instant.parse("2026-10-23T05:00:00Z"),NOW=INJECTED.plusSeconds(10),DEADLINE=INJECTED.plusSeconds(60);
    @Test void freshTicketKeepsSaveSourcesButMayMeasureFreshDriverIdentity() {
        assertDoesNotThrow(()->check(ticket(false,null),ticket(true,null)));
    }
    @Test void oldNonceOrPreInjectionReleaseCannotAuthorizeNewRead() {
        var nonce=row(true);nonce.put("nonce","1".repeat(32));
        assertThrows(IllegalArgumentException.class,()->check(ticket(false,null),ticket(true,nonce)));
        var early=row(true);early.put("observed_at_utc",INJECTED.minusSeconds(1).toString());
        assertThrows(IllegalArgumentException.class,()->check(ticket(false,null),ticket(true,early)));
    }
    @Test void callerSdkHashOrDifferentSaveCannotReplaceOriginalSourceTuple() {
        var sdk=row(true);sdk.set("sdk_freeze_ref",new ExactRef(ROOT.resolve("sdk-freeze.json").toString(),1,"b".repeat(64)).toJson());
        assertThrows(IllegalArgumentException.class,()->check(ticket(false,null),ticket(true,sdk)));
        var changed=row(true);changed.set("save_identity",new FileStatIdentity(BigInteger.ONE,"999","123").toJson());
        assertThrows(IllegalArgumentException.class,()->check(ticket(false,null),ticket(true,changed)));
    }
    @Test void outputMustBeTheNewExactOwnedNonceChildAndEarlierLease() {
        var output=row(true);output.put("output_root",ROOT.resolve("unowned-output").toString());
        assertThrows(IllegalArgumentException.class,()->check(ticket(false,null),ticket(true,output)));
        var later=row(true);later.put("review_at_utc",DEADLINE.plusSeconds(1).toString());
        assertThrows(IllegalArgumentException.class,()->check(ticket(false,null),ticket(true,later)));
    }
    private static void check(SavedProofReadTicket old,SavedProofReadTicket next) {
        ColdRawRestoreQualification.validateNewTicket(old,next,INJECTED,DEADLINE,OWNED,NOW);
    }
    private static SavedProofReadTicket ticket(boolean next,ObjectNode changed) {
        ObjectNode value=changed==null?row(next):changed;byte[] bytes=StrictJson.canonical(value);
        Path path=next?OWNED.resolve("RAW-RESTORE-SDK-READ-TICKET.json"):ROOT.resolve("ORIGINAL-SDK-READ-TICKET.json");
        return SavedProofReadTicket.parse(new RecoveryEvidence(new ExactRef(path.toString(),bytes.length,RecoveryEvidence.sha256(bytes)),bytes));
    }
    private static ObjectNode row(boolean next) {
        var value=StrictJson.object();String nonce=(next?"2":"1").repeat(32);
        value.put("schema",SavedProofReadTicket.SCHEMA);value.put("machine_id","synthetic-source-fixture-machine");value.put("nonce",nonce);
        value.put("observed_at_utc",(next?INJECTED.plusSeconds(1):INJECTED.minusSeconds(30)).toString());value.put("review_at_utc",DEADLINE.toString());
        value.put("driver_path",ROOT.resolve("state/native-session/driver-state.json").toString());
        value.set("driver_identity",new FileStatIdentity(BigInteger.ONE,next?"12":"11",next?"456":"123").toJson());
        value.set("save_ref",new ExactRef(ROOT.resolve("state/profile/save games/xar_checkpoint.ck3").toString(),1,"a".repeat(64)).toJson());
        value.set("save_identity",new FileStatIdentity(BigInteger.ONE,"22","123").toJson());value.put("sdk_root",ROOT.resolve("sdk").toString());
        value.set("sdk_freeze_ref",new ExactRef(ROOT.resolve("sdk-freeze.json").toString(),1,"a".repeat(64)).toJson());
        value.set("validator_ref",new ExactRef(ROOT.resolve("sdk/xar_autoplayer/cold_checkpoint_validator.py").toString(),1,"a".repeat(64)).toJson());
        value.put("pipe_name","synthetic-original-pipe");value.put("python_executable",ROOT.resolve("python.exe").toString());
        value.put("output_root",(next?OWNED.resolve("raw-sdk-"+nonce):ROOT.resolve("original-sdk-output")).toString());
        value.put("max_driver_bytes",1);value.put("physical_driver_reads",1);value.put("original_sdk_save_hash_calls",1);
        value.put("job_memory_limit_bytes",128L*1024*1024);value.put("timeout_seconds",20);return value;
    }
}
