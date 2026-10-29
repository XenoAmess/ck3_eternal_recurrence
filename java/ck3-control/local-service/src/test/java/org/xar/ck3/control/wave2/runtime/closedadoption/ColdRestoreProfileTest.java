package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Source-only profile semantics and real temporary-file failures; never a Root or Native grant. */
class ColdRestoreProfileTest {
    @TempDir Path temporary;
    private record Fixture(ObjectNode basis,ObjectNode manifest,ObjectNode prelaunch,ObjectNode dlc,
            ClosedInputsSessionAuthority.NativeRestoreInputs inputs,ExactRef dlcRef) { }
    private static ExactRef reference(Path path,ObjectNode value) {
        byte[] raw = StrictJson.canonical(value); return new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw));
    }
    private static Fixture fixture(ObjectNode basis) {
        var initial = NativeOwnerResumeSessionTest.inputs(basis);
        var paths = NativeOwnerResumeSession.sharedStatePaths(initial);
        ObjectNode dlc = StrictJson.object(); dlc.putArray("enabled_mods"); dlc.putArray("disabled_dlcs");
        ExactRef dlcRef = reference(paths.profileRoot().resolve("dlc_load.json"),dlc);
        ObjectNode manifest = StrictJson.object(); manifest.set("machine_id",basis.get("machine_id"));
        manifest.put("state_dir",paths.stateRoot().toString()); manifest.put("profile_dir",paths.profileRoot().toString());
        manifest.putObject("load_profile").put("dlc_load_sha256",dlcRef.sha256()).putArray("enabled_mods");
        manifest.putObject("mod").put("enabled",false).putArray("mounted_mods");
        manifest.putObject("rules").putArray("profile");
        String digest = ColdRestoreProfile.contractDigest(manifest); manifest.put("environment_sha256",digest);
        ((ObjectNode)basis.get("checkpoint").get("succession_lifecycle")).put("environment_sha256",digest);
        var inputs = NativeOwnerResumeSessionTest.inputs(basis);
        return new Fixture(basis,manifest,ColdRestoreProfile.prelaunch(inputs,digest),dlc,inputs,dlcRef);
    }
    private static Fixture fixture() throws IOException { return fixture(NativeOwnerResumeSessionTest.basis()); }
    private static void validate(Fixture f) { ColdRestoreProfile.validate(f.inputs(),f.manifest(),f.prelaunch(),f.dlc(),f.dlcRef()); }
    private static Fixture rebind(Fixture f) {
        String digest = ColdRestoreProfile.contractDigest(f.manifest()); f.manifest().put("environment_sha256",digest);
        ((ObjectNode)f.basis().get("checkpoint").get("succession_lifecycle")).put("environment_sha256",digest);
        var inputs = NativeOwnerResumeSessionTest.inputs(f.basis());
        return new Fixture(f.basis(),f.manifest(),ColdRestoreProfile.prelaunch(inputs,digest),f.dlc(),inputs,f.dlcRef());
    }
    @Test void originalProfileConsumerRequiresCompletePrelaunchAndPreservesSavedProgress() throws Exception {
        Fixture f = fixture(); assertDoesNotThrow(() -> validate(f));
        var wire=StrictJson.parse(StrictJson.canonical(f.prelaunch()));
        assertInstanceOf(ObjectNode.class,wire);
        assertDoesNotThrow(()->ColdRestoreProfile.validate(f.inputs(),f.manifest(),(ObjectNode)wire,f.dlc(),f.dlcRef()));
        ObjectNode wrongType=((ObjectNode)wire).deepCopy();wrongType.put("ordinary_cycle_credit",false);
        assertThrows(RuntimeException.class,()->ColdRestoreProfile.validate(f.inputs(),f.manifest(),wrongType,f.dlc(),f.dlcRef()));
        ObjectNode floating=((ObjectNode)wire).deepCopy();floating.put("ordinary_cycle_credit",0.0);
        assertThrows(RuntimeException.class,()->ColdRestoreProfile.validate(f.inputs(),f.manifest(),floating,f.dlc(),f.dlcRef()));
        assertEquals(5182,f.prelaunch().get("completed_cycles").intValue()); assertEquals(11541,f.prelaunch().get("next_sequence").intValue());
        assertEquals("native-40526-1bec95182886",f.basis().get("frame").get("episode_run_id").textValue());
        assertFalse(f.prelaunch().get("original_actions_replayed").booleanValue());
    }
    @Test void sharedStateMachineSemanticDigestAndCompletePrelaunchRejectDrift() throws Exception {
        for (String field : List.of("state_dir","profile_dir","machine_id","environment_sha256")) {
            Fixture f = fixture(); f.manifest().put(field,"changed"); assertThrows(RuntimeException.class,() -> validate(f));
        }
        for (String field : List.of("basis_ref","checkpoint","original_wall_start_utc","driver_close_ref","closure_ref")) {
            Fixture f = fixture(); f.prelaunch().remove(field); assertThrows(RuntimeException.class,() -> validate(f));
        }
        Fixture f = fixture(); f.prelaunch().put("approved",true); assertThrows(RuntimeException.class,() -> validate(f));
    }
    @Test void booleanModAndExactDlcProfileRejectWrongTypesContentsAndBytePin() throws Exception {
        Fixture f = fixture(); ((ObjectNode)f.manifest().get("mod")).put("enabled",0); Fixture changed = rebind(f);
        assertThrows(RuntimeException.class,() -> validate(changed));
        Fixture nonempty = fixture(); ((ArrayNode)nonempty.dlc().get("enabled_mods")).add("other.mod");
        assertThrows(RuntimeException.class,() -> validate(nonempty));
        Fixture pin = fixture(); ((ObjectNode)pin.manifest().get("load_profile")).put("dlc_load_sha256","f".repeat(64)); Fixture wrong = rebind(pin);
        assertThrows(RuntimeException.class,() -> validate(wrong));
    }
    @Test void mountedModsAndXarRulesCannotPassAsOriginalVanillaProfile() throws Exception {
        Fixture f = fixture(); ((ArrayNode)f.manifest().get("mod").get("mounted_mods")).add("other"); Fixture mounted = rebind(f);
        assertThrows(RuntimeException.class,() -> validate(mounted));
        Fixture rule = fixture(); ((ArrayNode)rule.manifest().get("rules").get("profile")).addObject().put("rule","xar_enabled"); Fixture xar = rebind(rule);
        assertThrows(RuntimeException.class,() -> validate(xar));
    }
    @Test void pythonAsciiDigestMatchesActualPythonOracleIncludingNonBmpKeysAndTransientFields() {
        ObjectNode input = StrictJson.object(); input.put("path","D:/synthetic/\u7430\u7130/\ud83d\udd25");
        input.put("prepared_at","ignored"); input.put("environment_sha256","ignored");
        input.putObject("persistent_tutorial_state").put("initialized_this_prepare",true).put("policy","preserve");
        input.put("\ue000",1); input.put("\ud800\udc00",2); input.put("del","\u007f");
        assertEquals("e59bc6e01b46f471a62182a712393690f6cb25db04c1db4d234d2ade98bb04ee",ColdRestoreProfile.contractDigest(input));
        input.put("prepared_at","another"); input.put("environment_sha256","another");
        ((ObjectNode)input.get("persistent_tutorial_state")).put("initialized_this_prepare",false);
        assertEquals("e59bc6e01b46f471a62182a712393690f6cb25db04c1db4d234d2ade98bb04ee",ColdRestoreProfile.contractDigest(input));
    }
    @Test void floatDigestIsExplicitlyUnavailableRatherThanRoundedOrNormalized() {
        ObjectNode input = StrictJson.object().put("value",1.0);
        var failure = assertThrows(RuntimeException.class,() -> ColdRestoreProfile.contractDigest(input));
        assertTrue(failure.getMessage().contains("UNAVAILABLE"));
    }
    @Test void actualProducerPinsSyntheticProfileAndRejectsDriftWithoutAnyDriverOrSaveOpen() throws Exception {
        ObjectNode basis = NativeOwnerResumeSessionTest.basis(); Path state = temporary.resolve("shared-state");
        Path driver = state.resolve("native-session/driver-state.json"),save = state.resolve("profile/save games/xar_checkpoint.ck3");
        ((ObjectNode)basis.get("refs").get("driver")).put("path",driver.toString());
        ((ObjectNode)basis.get("refs").get("save")).put("path",save.toString());
        ((ObjectNode)basis.get("checkpoint")).put("path",save.toString());
        Fixture f = fixture(basis); Path runtime = f.inputs().runtimeRoot();
        // Change only the new graph's data tuple to the owned temporary directory; original shared state is distinct.
        var original = f.inputs(); runtime = temporary.resolve("new-graph");
        var inputs = new ClosedInputsSessionAuthority.NativeRestoreInputs(runtime,original.plan(),original.quote(),original.preflight(),
                original.attemptNonce(),original.taskNonce(),original.basis(),original.qualificationRef(),original.committedHeadRef(),
                original.pipeName(),original.entrypoint(),original.sdkRoot(),original.sdkFreeze());
        Files.createDirectories(state.resolve("profile")); Files.createDirectories(runtime);
        Path manifest = state.resolve("profile/xar-autoplayer-environment.json");
        Files.write(manifest,StrictJson.canonical(f.manifest())); Files.write(state.resolve("profile/dlc_load.json"),StrictJson.canonical(f.dlc()));
        ObjectNode pre = ColdRestoreProfile.prelaunch(inputs,f.manifest().get("environment_sha256").textValue());
        Path prePath = runtime.resolve("ROOT-C23-COLD-PRELAUNCH.json"); Files.write(prePath,StrictJson.canonical(pre));
        ExactRef ref = reference(prePath,pre);
        var verified = ColdRestoreProfile.verify(inputs,ref);
        assertEquals(reference(manifest,f.manifest()),verified.manifestRef()); assertEquals(3,verified.sourcePins().size());
        assertDoesNotThrow(verified::requireUnchanged);
        Files.createDirectory(state.resolve("profile/mod")); Files.writeString(state.resolve("profile/mod/unexpected.mod"),"unexpected");
        assertThrows(RuntimeException.class,verified::requireUnchanged);
        Files.delete(state.resolve("profile/mod/unexpected.mod"));
        Files.writeString(state.resolve("profile/dlc_load.json"),"{}");
        assertThrows(RuntimeException.class,verified::requireUnchanged);
        assertFalse(Files.exists(driver)); assertFalse(Files.exists(save));
    }
}
