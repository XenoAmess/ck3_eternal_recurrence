package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Actual finite shared-profile verifier. Called by the retained writer while its original lock is held. */
final class ColdRestoreProfile {
    private static final int LIMIT = 262_144;
    private ColdRestoreProfile() { }
    private record Read(ExactRef reference, FileStatIdentity identity, byte[] bytes) { }
    static final class Verified {
        private final ExactRef manifest;
        private final List<Read> reads;
        private final Path modDirectory;
        private Verified(ExactRef manifest,List<Read> reads,Path modDirectory) {
            this.manifest = manifest; this.reads = List.copyOf(reads); this.modDirectory = modDirectory;
        }
        ExactRef manifestRef() { return manifest; }
        List<ExactRef> sourcePins() { return reads.stream().map(Read::reference).toList(); }
        void requireUnchanged() throws IOException {
            for (Read previous : reads) {
                Read current = read(Path.of(previous.reference().path()),LIMIT);
                StrictJson.require(current.reference().equals(previous.reference()) && current.identity().equals(previous.identity()),
                        "original cold profile source bytes and native identity remain unchanged");
            }
            emptyModDirectory(modDirectory);
        }
    }
    static Verified verify(ClosedInputsSessionAuthority.NativeRestoreInputs inputs,ExactRef quotedPrelaunch) throws IOException {
        var paths = NativeOwnerResumeSession.sharedStatePaths(inputs);
        StrictJson.require(Path.of(quotedPrelaunch.path()).equals(inputs.runtimeRoot().resolve("ROOT-C23-COLD-PRELAUNCH.json")),
                "actual quoted shared prelaunch path");
        List<Read> reads = new ArrayList<>();
        Read manifest = read(paths.environmentManifest(),LIMIT); reads.add(manifest);
        Read prelaunch = read(Path.of(quotedPrelaunch.path()),RecoveryEvidence.MAX_BYTES); reads.add(prelaunch);
        StrictJson.require(prelaunch.reference().equals(quotedPrelaunch),"actual Prepared quote pins complete original prelaunch");
        Read dlc = read(paths.profileRoot().resolve("dlc_load.json"),RecoveryEvidence.MAX_BYTES); reads.add(dlc);
        ObjectNode body = object(StrictJson.parse(manifest.bytes(),LIMIT));
        ObjectNode pre = object(StrictJson.parse(prelaunch.bytes()));
        validate(inputs,body,pre,StrictJson.parse(dlc.bytes()),dlc.reference());
        // A reviewed absence proof is an independent binder overlay in the original runtime.
        // Never inject it into this base manifest or change its frozen semantic digest here.
        Path modDirectory = paths.profileRoot().resolve("mod"); emptyModDirectory(modDirectory);
        Verified result = new Verified(manifest.reference(),reads,modDirectory);
        result.requireUnchanged(); return result;
    }
    /** Single pure consumer shared with the actual filesystem producer and bounded source regressions. */
    static void validate(ClosedInputsSessionAuthority.NativeRestoreInputs inputs,ObjectNode manifest,ObjectNode prelaunch,
            JsonNode dlcLoad,ExactRef dlcRef) {
        var paths = NativeOwnerResumeSession.sharedStatePaths(inputs);
        ObjectNode basis = object(StrictJson.parse(inputs.basis().bytes()));
        String environment = StrictJson.text(basis.get("checkpoint").get("succession_lifecycle").get("environment_sha256"));
        StrictJson.require(StrictJson.text(manifest.get("machine_id")).equals(StrictJson.text(basis.get("machine_id")))
                && Path.of(StrictJson.text(manifest.get("state_dir"))).equals(paths.stateRoot())
                && Path.of(StrictJson.text(manifest.get("profile_dir"))).equals(paths.profileRoot())
                && environment.equals(StrictJson.text(manifest.get("environment_sha256")))
                && environment.equals(contractDigest(manifest)),"original same-machine shared-state environment semantic digest");
        // Jackson integer node subclasses share one JSON integer domain. A file roundtrip must preserve that domain.
        StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(prelaunch,RecoveryEvidence.MAX_BYTES),
                StrictJson.canonical(prelaunch(inputs,environment),RecoveryEvidence.MAX_BYTES)),
                "complete original shared saved prelaunch, not a marker");
        ObjectNode load = object(manifest.get("load_profile"));
        StrictJson.require(load.get("enabled_mods") != null && load.get("enabled_mods").isArray() && load.get("enabled_mods").isEmpty(),
                "current cold profile has explicitly empty enabled mods");
        ObjectNode mod = StrictJson.object(manifest.get("mod"),Set.of("enabled","mounted_mods"));
        StrictJson.require(mod.get("enabled").isBoolean() && !mod.get("enabled").booleanValue()
                && mod.get("mounted_mods").isArray() && mod.get("mounted_mods").isEmpty(),"exact original vanilla mod profile");
        ObjectNode dlc = StrictJson.object(dlcLoad,Set.of("enabled_mods","disabled_dlcs"));
        StrictJson.require(dlc.get("enabled_mods").isArray() && dlc.get("enabled_mods").isEmpty()
                && dlc.get("disabled_dlcs").isArray() && dlc.get("disabled_dlcs").isEmpty()
                && Path.of(dlcRef.path()).equals(paths.profileRoot().resolve("dlc_load.json"))
                && StrictJson.text(load.get("dlc_load_sha256")).equals(dlcRef.sha256()),"actual original dlc_load bytes and empty profile");
        JsonNode profile = object(manifest.get("rules")).get("profile");
        StrictJson.require(profile != null && profile.isArray(),"actual complete game rule profile");
        for (JsonNode rule : profile) {
            StrictJson.require(!StrictJson.text(object(rule).get("rule")).startsWith("xar_"),"no XAR rules in the actual ordinary vanilla cold profile");
        }
        StrictJson.require("ordinary_campaign_succession".equals(StrictJson.text(basis.get("checkpoint").get("succession_lifecycle").get("lifecycle"))),
                "this migrated cold-profile route preserves the original ordinary-only producer boundary");
        ObjectNode expectedLife = StrictJson.object(); expectedLife.put("schema","xar.ck3.succession-lifecycle-binding/v1");
        expectedLife.put("lifecycle","ordinary_campaign_succession"); expectedLife.putNull("xar_enabled");
        expectedLife.put("pact_contract","absent_by_verified_xar_mod_not_loaded");
        expectedLife.put("source","absent_by_verified_xar_mod_not_loaded"); expectedLife.put("environment_sha256",environment);
        StrictJson.require(expectedLife.equals(basis.get("checkpoint").get("succession_lifecycle")),
                "all six original lifecycle fields match the actual no-XAR-rule environment binding");
    }
    static ObjectNode prelaunch(ClosedInputsSessionAuthority.NativeRestoreInputs inputs,String environment) {
        var basis = object(StrictJson.parse(inputs.basis().bytes()));
        var result = StrictJson.object(); result.put("schema","xar.current-saved-cold-prelaunch/v1");
        result.set("machine_id",basis.get("machine_id")); result.put("status","CLOSED_CURRENT_SAVED_CHECKPOINT_VALIDATED");
        result.set("basis_ref",inputs.basis().reference().toJson()); result.set("validation_ref",inputs.qualificationRef().toJson());
        result.set("checkpoint",basis.get("checkpoint")); result.put("environment_sha256",environment); result.put("pipe_name",inputs.pipeName());
        result.set("original_wall_start_utc",basis.get("origin").get("original_wall_origin_utc"));
        for (String key : List.of("completed_cycles","next_sequence")) { result.set(key,basis.get(key)); }
        result.set("date_raw",basis.get("frame").get("date_raw"));
        result.set("driver_close_ref",basis.get("refs").get("driver_close")); result.set("closure_ref",basis.get("refs").get("closure"));
        result.put("ordinary_cycle_credit",0); result.put("game_day_credit",0); result.put("original_actions_replayed",false);
        result.put("power_loss_durability","not_asserted"); return result;
    }
    static String contractDigest(ObjectNode manifest) {
        ObjectNode stable = manifest.deepCopy(); stable.remove("prepared_at"); stable.remove("environment_sha256");
        if (stable.get("persistent_tutorial_state") instanceof ObjectNode tutorial) { tutorial.remove("initialized_this_prepare"); }
        // Python environment.snapshot_digest uses ensure_ascii=True, unlike the shared wire encoder.
        StringBuilder encoded = new StringBuilder(); appendPython(stable,encoded);
        String unicode = encoded.toString();
        StringBuilder ascii = new StringBuilder();
        for (int index = 0; index < unicode.length(); index++) {
            char value = unicode.charAt(index);
            if (value >= 0x7f) {
                ascii.append("\\u"); String hex = Integer.toHexString(value); ascii.append("0".repeat(4 - hex.length())).append(hex);
            } else { ascii.append(value); }
        }
        return RecoveryEvidence.sha256(ascii.toString().getBytes(StandardCharsets.US_ASCII));
    }
    private static void appendPython(JsonNode value,StringBuilder result) {
        StrictJson.require(value != null,"complete JSON value for original environment digest");
        if (value.isObject()) {
            List<String> keys = new ArrayList<>(); value.fieldNames().forEachRemaining(keys::add);
            keys.sort(ColdRestoreProfile::compareCodePoints); result.append('{'); boolean first = true;
            for (String key : keys) {
                if (!first) { result.append(','); } first = false;
                result.append(new String(StrictJson.canonical(com.fasterxml.jackson.databind.node.TextNode.valueOf(key)),StandardCharsets.UTF_8));
                result.append(':'); appendPython(value.get(key),result);
            }
            result.append('}');
        } else if (value.isArray()) {
            result.append('['); boolean first = true;
            for (JsonNode child : value) { if (!first) { result.append(','); } first = false; appendPython(child,result); }
            result.append(']');
        } else {
            StrictJson.require(!value.isFloatingPointNumber(),"UNAVAILABLE: floating environment number has no migrated Python digest profile");
            result.append(new String(StrictJson.canonical(value,LIMIT),StandardCharsets.UTF_8));
        }
        StrictJson.require(result.length() <= LIMIT,"finite original environment semantic encoding");
    }
    private static int compareCodePoints(String left,String right) {
        int first = 0,second = 0;
        while (first < left.length() && second < right.length()) {
            int a = left.codePointAt(first),b = right.codePointAt(second);
            if (a != b) { return Integer.compare(a,b); }
            first += Character.charCount(a); second += Character.charCount(b);
        }
        return Integer.compare(left.length() - first,right.length() - second);
    }
    private static void emptyModDirectory(Path directory) throws IOException {
        if (!Files.exists(directory,LinkOption.NOFOLLOW_LINKS)) { return; }
        StrictJson.require(Files.isDirectory(directory,LinkOption.NOFOLLOW_LINKS) && !Files.isSymbolicLink(directory),"ordinary isolated mod directory");
        try (var children = Files.list(directory)) { StrictJson.require(children.findAny().isEmpty(),"no mounted local mod payload"); }
    }
    private static Read read(Path path,int bound) throws IOException {
        var identities = new WindowsSavedProofIdentityReader(); var before = identities.stat(path);
        StrictJson.require(before.bytes().signum() > 0 && before.bytes().compareTo(java.math.BigInteger.valueOf(bound)) <= 0,
                "finite original cold-profile metadata only");
        byte[] raw; try (var input = Files.newInputStream(path)) { raw = input.readNBytes(bound + 1); }
        StrictJson.require(raw.length <= bound && before.bytes().longValueExact() == raw.length && before.equals(identities.stat(path)),
                "unchanged native cold-profile source identity");
        return new Read(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),before,raw);
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode,"original complete JSON object"); return (ObjectNode)value;
    }
}
