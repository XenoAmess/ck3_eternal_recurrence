package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseManifest;
import static org.xar.ck3.control.nativebridge.capabilities.army.CombatProjectionJson.*;

/** Original managed singleton/stock-source proof. Disk/source facts cannot mint a proof without the actual final frame probe. */
public final class CombatLoadedPlaysetProof {
    private CombatLoadedPlaysetProof() { }
    private static final String SCOPE="managed-session-single-mod-stock-phase-event-sources",DESCRIPTOR="mod/xar_autoplayer.mod",MARKER="suspended launch active; removed only after authenticated tree shutdown";
    private static final Pattern REPLACE=Pattern.compile("(?im)^\\s*replace_path\\s*=\\s*\"([^\"\\r\\n]+)\"\\s*$"),TARGET=Pattern.compile("(?im)^\\s*path\\s*=\\s*\"([^\"\\r\\n]+)\"\\s*$");
    @FunctionalInterface public interface CurrentProbe {Complete current()throws IOException;}
    /** Package-private original test-input seam. It returns JSON only and cannot mint Evidence. */
    record Definition(String canonicalSha,String gameVersion,String executableSha,List<StockPhaseManifest.Source> files,List<StockPhaseManifest.Source> feedback) {
        Definition {files=List.copyOf(files);feedback=List.copyOf(feedback);need(canonicalSha.equals(StockPhaseManifest.SHA256)&&files.size()==11&&feedback.size()==2&&feedback.get(0).relativePath().equals("common/on_action/accolade_on_actions.txt")&&feedback.get(1).relativePath().equals("events/accolade_events.txt"),"phase/accolade source closure drifted");}
    }
    /** Only this collector mints evidence; JSON decoding cannot construct a verified one. */
    public static final class Evidence {
        private final Complete current;private final Obj value;
        private Evidence(Complete current,Obj value){this.current=Objects.requireNonNull(current);this.value=Objects.requireNonNull(value);}
        public Obj value(){return value;}
        public void requireFrame(Complete actual){need(same(current,actual),"loaded playset proof differs from actual frame/source/session/connection");}
    }
    /** The actual owner must supply its state path and same physical current-frame probe; this does not install a runtime provider. */
    public static CombatPublicProjection.LoadedPlaysetSource managed(Path actualStateDir,CurrentProbe actualProbe) {
        Objects.requireNonNull(actualStateDir);Objects.requireNonNull(actualProbe);need(actualStateDir.isAbsolute(),"actual managed state path required");
        return input->collect(actualStateDir,input,actualProbe);
    }
    /** This is the original observed no-state-directory branch, not a fallback inside the protocol encoder. */
    public static Evidence unavailable(Complete actual,String actualReason){return new Evidence(actual,negative(actual,actualReason));}
    public static Evidence collect(Path actualStateDir,CombatPublicProjection.Input input,CurrentProbe actualProbe)throws IOException {
        Objects.requireNonNull(input);Objects.requireNonNull(actualProbe);
        try {
            ObjectNode proof=build(actualStateDir,input.after(),stock());Complete latest=Objects.requireNonNull(actualProbe.current());
            if(!same(input.after(),latest)||!yes(OpportunityJson.toNode(latest.semantic()).get("paused")))return unavailable(input.after(),"snapshot_changed_during_loaded_playset_proof");
            return new Evidence(latest,immutable(proof));
        } catch(IOException|IllegalArgumentException invalid) {
            // Original Service exposes the concrete collection failure. Never upgrade it to a verified claim.
            return unavailable(input.after(),(invalid instanceof IOException?"OSError":"LoadedPlaysetProofError")+": "+Objects.toString(invalid.getMessage(),invalid.getClass().getSimpleName()));
        }
    }
    public static Obj negative(Complete actual,String reason) {
        JsonNode episode=OpportunityJson.toNode(actual.semantic()).get("episode_run_id");return negativeForEpisode(episode!=null&&episode.isTextual()&&!episode.textValue().isEmpty()?java.util.Optional.of(episode.textValue()):java.util.Optional.empty(),reason);
    }
    public static Obj negativeForEpisode(java.util.Optional<String> episode,String actualReason) {
        Objects.requireNonNull(episode);var proof=obj().put("schema_version",2).put("status","unavailable").put("proof_scope",SCOPE).putNull("environment_sha256").put("unavailable_reason",actualReason==null||actualReason.isEmpty()?"proof_unavailable":actualReason);
        if(episode.isPresent()&&!episode.orElseThrow().isEmpty())proof.put("episode_run_id",episode.orElseThrow());else proof.putNull("episode_run_id");proof.putObject("claims").put("loaded_playset_verified",false);proof.put("proof_sha256",digest(proof,false).toUpperCase(Locale.ROOT));return immutable(proof);
    }
    private static Definition stock() {
        var m=StockPhaseManifest.load();var p=m.toJson();return new Definition(m.canonicalSha256(),text(p.get("game_version")),text(p.get("executable_sha256")),m.sources(),List.of(
                new StockPhaseManifest.Source("common/on_action/accolade_on_actions.txt","E41BB5D345F319C2B889E42CB578599E1763C57B89782566859679100340AAE5",11),
                new StockPhaseManifest.Source("events/accolade_events.txt","0E5ED632DF2ADE40EBFAE687BA61518447397E10D59BC1FFF8F5D9B44A5AFDCF",12)));
    }
    static Obj projectOriginalFiles(Path requested,Complete complete,Definition definition)throws IOException {return immutable(build(requested,complete,definition));}
    private static ObjectNode build(Path requested,Complete complete,Definition manifest)throws IOException {
        Path root=requested.toRealPath(),profile=root.resolve("profile").toRealPath();ObjectNode snapshot=object(OpportunityJson.toNode(complete.semantic()));String episode=nonempty(snapshot.get("episode_run_id"));
        var binding=obj();copy(snapshot,binding,"snapshot_id revision native_revision");nonempty(binding.get("snapshot_id"));nonnegative(binding.get("revision"));nonnegative(binding.get("native_revision"));
        ObjectNode hello=object(snapshot.path("diagnostics").get("hello"));BigInteger pid=positive(hello.get("pid")),generation=nonnegative(hello.get("session_generation"));need(yes(hello.get("ck3_build_match"))&&"ready".equals(text(hello.get("game_adapter_status"))),"native hello exact-build adapter is not ready");String version=nonempty(hello.get("expected_ck3_version")),expectedExe=shaText(hello.get("expected_ck3_sha256"));
        need(pid.equals(BigInteger.valueOf(complete.identity().game().pid())),"native hello is not the actual complete physical Game");
        Path environmentPath=profile.resolve("xar-autoplayer-environment.json");ObjectNode env=read(environmentPath);String environmentSha=nonempty(env.get("environment_sha256"));need(environmentSha.matches("[0-9A-Fa-f]{64}")&&environmentSha.equals(contractDigest(env)),"managed environment contract fingerprint differs");need(text(env.get("state_dir")).equals(root.toString())&&text(env.get("profile_dir")).equals(profile.toString()),"managed environment belongs to another state/profile directory");
        JsonNode game=env.get("game");need(manifest.gameVersion().equals(text(game.get("raw_version"))),"managed environment game version differs from phase manifest");Path executable=Path.of(nonempty(game.get("executable"))).toRealPath();need(executable.getFileName().toString().equalsIgnoreCase("ck3.exe")&&executable.getParent().getFileName().toString().equalsIgnoreCase("binaries"),"managed executable path is not CK3 binaries/ck3.exe");Path gameDir=executable.getParent().getParent();String exeSha=hash(executable,true),manifestExe=manifest.executableSha();need(shaText(game.get("executable_sha256")).equals(manifestExe)&&exeSha.equals(manifestExe)&&version.equals(manifest.gameVersion())&&expectedExe.equals(manifestExe),"managed/native CK3 exact-build identity differs from phase manifest");
        Path launchPath=root.resolve("control/ck3.json"),markerPath=root.resolve("control/unsafe-cleanup.json");ObjectNode launch=read(launchPath),marker=read(markerPath);keys(launch,Set.of("format_version","nonce","ck3_pid","parent_pid","executable","creation_date"));need(integer(launch.get("format_version")).equals(BigInteger.ONE),"managed launch record version is malformed");String nonce=nonempty(launch.get("nonce"));need(nonce.matches("[0-9a-f]{32}"),"managed launch nonce is malformed");need(positive(launch.get("ck3_pid")).equals(pid),"native bridge PID differs from the managed launch record");positive(launch.get("parent_pid"));need(Path.of(nonempty(launch.get("executable"))).toRealPath().equals(executable),"managed launch executable differs from the environment");nonempty(launch.get("creation_date"));
        keys(marker,Set.of("nonce","ck3_pid","reason"));need(eq(marker.get("nonce"),launch.get("nonce"))&&eq(marker.get("ck3_pid"),launch.get("ck3_pid"))&&MARKER.equals(text(marker.get("reason"))),"managed active-session marker differs from the launch record");
        JsonNode loadProfile=object(env.get("load_profile"));Path dlcPath=profile.resolve("dlc_load.json");ObjectNode dlc=read(dlcPath);var enabled=obj().arrayNode().add(DESCRIPTOR);need(dlc.size()==2&&eq(dlc.get("enabled_mods"),enabled)&&dlc.has("disabled_dlcs")&&array(dlc.get("disabled_dlcs")).isEmpty()&&eq(loadProfile.get("enabled_mods"),enabled)&&array(loadProfile.get("disabled_dlcs")).isEmpty(),"managed enabled_mods is not the exact xar_autoplayer singleton");String dlcSha=hash(dlcPath,false);need(dlcSha.equals(text(loadProfile.get("dlc_load_sha256"))),"managed dlc_load.json bytes differ from the environment binding");
        Path outer=profile.resolve(DESCRIPTOR);String outerSha=hash(outer,false);need(text(loadProfile.get("outer_descriptor")).equals(outer.toRealPath().toString())&&outerSha.equals(text(loadProfile.get("outer_descriptor_sha256"))),"managed outer descriptor differs from the environment binding");
        var matcher=TARGET.matcher(readText(outer));need(matcher.find(),"managed outer descriptor target is malformed");Path production=Path.of(matcher.group(1)).toRealPath();need(!matcher.find(),"managed outer descriptor target is duplicated");need(text(env.path("mod").get("production_path")).equals(production.toString())&&production.startsWith(profile),"managed production path differs or escapes isolated profile");
        ObjectNode tree=obj();try(var paths=Files.walk(production)){for(Path path:paths.filter(Files::isRegularFile).sorted().toList()){var row=tree.putObject(production.relativize(path).toString().replace('\\','/'));row.put("size",Files.size(path)).put("sha256",hash(path,false));}}
        String treeSha=digest(tree,true);JsonNode mod=object(env.get("mod"));need(treeSha.equals(text(mod.get("production_tree_sha256")))&&integer(mod.get("production_file_count")).equals(BigInteger.valueOf(tree.size())),"managed production tree differs from the environment binding");Path inner=production.resolve("descriptor.mod");String innerText=readText(inner);need(!innerText.contains("remote_file_id"),"production descriptor contains remote_file_id");List<String> replacePaths=new ArrayList<>();var replaces=REPLACE.matcher(innerText);while(replaces.find()){String canonical=relative(replaces.group(1));need(replacePaths.stream().noneMatch(p->p.equalsIgnoreCase(canonical)),"production descriptor repeats replace_path");replacePaths.add(canonical);}
        List<StockPhaseManifest.Source> sources=new ArrayList<>(manifest.files());sources.addAll(manifest.feedback());
        var stock=obj().arrayNode();for(var source:sources) {
            String relative=relative(source.relativePath());boolean overlay=false;var names=tree.fieldNames();while(names.hasNext())if(names.next().equalsIgnoreCase(relative))overlay=true;List<String> conflicts=new ArrayList<>();for(String prefix:replacePaths)if(relative.equalsIgnoreCase(prefix)||relative.toLowerCase(Locale.ROOT).startsWith(prefix.toLowerCase(Locale.ROOT)+"/"))conflicts.add(prefix);
            String stockSha=hash(gameDir.resolve("game").resolve(relative),true);need(stockSha.equals(source.sha256()),"stock phase-event source hash differs: "+relative);need(!overlay,"production tree overlays combat feedback sources: "+relative);need(conflicts.isEmpty(),"production descriptor replace_path covers combat feedback sources: "+relative);
            var row=stock.addObject().put("load_order",source.loadOrder()).put("source_kind",source.loadOrder()<11?"phase_event_manifest":"accolade_feedback_closure").put("relative_path",relative).put("manifest_sha256",source.sha256()).put("stock_sha256",stockSha).put("production_overlay_present",overlay);strings(row,"replace_path_conflicts",conflicts);
        }
        var proof=obj().put("schema_version",2).put("status","verified").put("proof_scope",SCOPE).put("episode_run_id",episode).put("environment_sha256",environmentSha).put("environment_manifest_bytes_sha256",hash(environmentPath,true)).put("phase_event_manifest_sha256",manifest.canonicalSha());proof.set("snapshot_binding",binding);
        var managed=proof.putObject("managed_session").put("native_bridge_pid",pid).put("native_session_generation",generation).put("launch_nonce",nonce).put("launch_record_sha256",hash(launchPath,true)).put("active_session_marker_sha256",hash(markerPath,true)).put("state_dir",root.toString()).put("profile_dir",profile.toString()).put("executable",executable.toString()).put("executable_sha256",exeSha).put("active_marker_reason",MARKER);managed.set("launch_creation_date",launch.get("creation_date").deepCopy());
        var dl=proof.putObject("dlc_load").put("relative_path","dlc_load.json").put("sha256",dlcSha.toUpperCase(Locale.ROOT)).put("exact_singleton",true);dl.set("enabled_mods",enabled);dl.putArray("disabled_dlcs");
        var pm=proof.putObject("production_mod").put("descriptor_ref",DESCRIPTOR).put("outer_descriptor_sha256",outerSha.toUpperCase(Locale.ROOT)).put("production_root",production.toString()).put("production_tree_sha256",treeSha.toUpperCase(Locale.ROOT)).put("production_file_count",tree.size()).put("inner_descriptor_sha256",hash(inner,true)).put("phase_source_overlay_count",0).put("phase_source_replace_path_conflict_count",0).put("accolade_feedback_source_overlay_count",0).put("accolade_feedback_replace_path_conflict_count",0);strings(pm,"replace_paths",replacePaths);
        var ss=proof.putObject("stock_sources").put("game_root",gameDir.toString()).put("count",stock.size()).put("phase_manifest_count",11).put("accolade_feedback_closure_count",2);ss.set("files",stock);
        var claims=proof.putObject("claims");for(String key:List.of("managed_session_pid_bound","episode_environment_bound","enabled_mods_exact_singleton","production_phase_source_overlays_absent","production_replace_path_conflicts_absent","stock_source_sha256_exact","accolade_feedback_source_closure_verified","loaded_playset_verified"))claims.put(key,true);proof.putNull("unavailable_reason");proof.put("proof_sha256",digest(proof,false).toUpperCase(Locale.ROOT));return proof;
    }
    private static boolean same(Complete a,Complete b){return a.identity().equals(b.identity())&&a.source().equals(b.source())&&a.sessionId().equals(b.sessionId())&&a.connectionGeneration().equals(b.connectionGeneration());}
    private static String relative(String raw){String s=raw.replace('\\','/');need(!s.isEmpty()&&!s.startsWith("/")&&!s.endsWith("/")&&!s.contains("//"),"source is not a canonical relative path");for(String part:s.split("/"))need(!part.equals(".")&&!part.equals(".."),"source is not canonical");return s;}
    private static String nonempty(JsonNode n){String value=text(n);need(!value.isEmpty(),"nonempty original proof string required");return value;}
    private static BigInteger nonnegative(JsonNode n){var v=integer(n);need(v.signum()>=0,"nonnegative original proof integer required");return v;}
    private static BigInteger positive(JsonNode n){var v=nonnegative(n);need(v.signum()>0,"positive original proof integer required");return v;}
    private static String shaText(JsonNode n){String s=nonempty(n).toUpperCase(Locale.ROOT);need(s.matches("[0-9A-F]{64}"),"original proof SHA malformed");return s;}
    private static void keys(ObjectNode n,Set<String> expected){var actual=new java.util.HashSet<String>();n.fieldNames().forEachRemaining(actual::add);need(actual.equals(expected),"original managed proof field contract differs");}
    private static ObjectNode read(Path p)throws IOException {byte[] body=Files.readAllBytes(p);return object(FullJsonTree.parse(body,64<<20));}
    private static String readText(Path p)throws IOException {String s=Files.readString(p,StandardCharsets.UTF_8);return s.startsWith("\ufeff")?s.substring(1):s;}
    private static String hash(Path p,boolean upper)throws IOException {try{MessageDigest d=MessageDigest.getInstance("SHA-256");try(var stream=Files.newInputStream(p)){byte[] b=new byte[1<<20];int n;while((n=stream.read(b))!=-1)d.update(b,0,n);}String s=HexFormat.of().formatHex(d.digest());return upper?s.toUpperCase(Locale.ROOT):s;}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    private static String contractDigest(ObjectNode environment){var stable=environment.deepCopy();stable.remove(List.of("prepared_at","environment_sha256"));JsonNode tutorial=stable.get("persistent_tutorial_state");if(tutorial instanceof ObjectNode t)t.remove("initialized_this_prepare");return digest(stable,true);}
    private static String digest(ObjectNode n,boolean ascii){byte[] bytes=canonicalProof(n);if(ascii){String s=new String(bytes,StandardCharsets.UTF_8);StringBuilder escaped=new StringBuilder();for(char c:s.toCharArray())if(c>127)escaped.append(String.format(Locale.ROOT,"\\u%04x",(int)c));else escaped.append(c);bytes=escaped.toString().getBytes(StandardCharsets.US_ASCII);}try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}

    /** Scoped canonical serializer for proof objects; preserves StrictJson semantics but allows >1MiB output. */
    private static byte[] canonicalProof(JsonNode value) {
        StringBuilder output = new StringBuilder();
        appendProof(value, output);
        byte[] raw = output.toString().getBytes(StandardCharsets.UTF_8);
        need(raw.length <= 64 << 20, "canonical proof exceeds 64MiB lease");
        return raw;
    }

    private static void appendProof(JsonNode value, StringBuilder output) {
        need(value != null, "missing JSON node cannot be serialized as null");
        if (value.isObject()) {
            output.append('{');
            TreeSet<String> keys = new TreeSet<>();
            value.fieldNames().forEachRemaining(keys::add);
            boolean first = true;
            for (String key : keys) {
                if (!first) { output.append(','); }
                first = false;
                quoteProof(key, output);
                output.append(':');
                appendProof(value.get(key), output);
            }
            output.append('}');
        } else if (value.isArray()) {
            output.append('[');
            boolean first = true;
            for (JsonNode entry : value) {
                if (!first) { output.append(','); }
                first = false;
                appendProof(entry, output);
            }
            output.append(']');
        } else if (value.isTextual()) {
            quoteProof(value.textValue(), output);
        } else if (value.isIntegralNumber()) {
            output.append(value.bigIntegerValue());
        } else if (value.isBoolean()) {
            output.append(value.booleanValue() ? "true" : "false");
        } else if (value.isNull()) {
            output.append("null");
        } else {
            throw new ContractViolationException("non-integer JSON number is outside this canonical contract");
        }
    }

    private static void quoteProof(String value, StringBuilder output) {
        // Empty strings are valid JSON values; contracts decide whether they are allowed.
        if (!value.isEmpty()) { StrictJson.text(value); }
        output.append('"');
        String hexadecimal = "0123456789abcdef";
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            switch (current) {
                case '"' -> output.append("\\\"");
                case '\\' -> output.append("\\\\");
                case '\b' -> output.append("\\b");
                case '\f' -> output.append("\\f");
                case '\n' -> output.append("\\n");
                case '\r' -> output.append("\\r");
                case '\t' -> output.append("\\t");
                default -> {
                    if (current < 0x20) {
                        output.append("\\u00").append(hexadecimal.charAt(current >> 4))
                                .append(hexadecimal.charAt(current & 15));
                    } else { output.append(current); }
                }
            }
        }
        output.append('"');
    }
    private static void need(boolean ok,String reason){StrictJson.require(ok,reason);}
}
