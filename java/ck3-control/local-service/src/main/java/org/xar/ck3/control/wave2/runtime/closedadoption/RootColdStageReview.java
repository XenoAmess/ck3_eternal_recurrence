package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Independent actual Root review for a specific cold submission; a planned command is data only. */
public final class RootColdStageReview {
    private static final int LIMIT=StrictJson.EXPLICIT_MAX_BYTES;
    public enum Stage { SAVED_GAME_CREATE, MOD_ABSENCE_ROOT_REVIEW, MCP_OWNER, INJECT, RAW_PREFLIGHT, CAPABILITIES_POSTSTATE }
    public enum Effect {
        ARCHIVE_THREE_ORIGINAL_ENGINE_LOGS, CREATE_ORIGINAL_GAME_ONCE, LOAD_EXISTING_CHECKPOINT,
        START_ORIGINAL_MCP_OWNER_ONCE, ORIGINAL_DRIVER_CONSTRUCTOR_AND_SOURCE_READS,
        LOAD_HELD_DLL_AND_DELIVER_NATIVE_HELLO, HELLO_MAY_READ_OR_REPLACE_DRIVER_AND_WAL,
        HELLO_MAY_UPDATE_JOURNAL_OR_REMOVE_MANAGED_RESTORE_MARKER,
        ONE_BOOTSTRAP_CAP_MAY_PERSIST_DRIVER, VERIFY_ACTUAL_CURRENT_GAME_HEADER_AFTER_COMPLETED_CAP,
        KEEP_ORIGINAL_BASIS_CHECKPOINT_AND_EPISODE,
        INDEPENDENT_ROOT_CONFIRMS_KNOWN_EMPTY_MODS_FROM_EXACT_PROFILE_AND_STARTUP_SNAPSHOT,
        UNKNOWN_NEVER_REPLAY, NO_WARM_OR_BUSINESS_GRANT
    }
    public record PlannedCommand(WindowsJobProcess.CommandSpec command, ExactRef executable,
            List<ExactRef> immutableInputs, Instant deadline) {
        public PlannedCommand {
            Objects.requireNonNull(command); Objects.requireNonNull(executable); Objects.requireNonNull(deadline);
            immutableInputs = List.copyOf(immutableInputs);
            StrictJson.require(Path.of(executable.path()).equals(command.executable()) && !immutableInputs.isEmpty()
                    && immutableInputs.size() <= 2048 && command.memoryLimitBytes() <= StrictJson.MAX_SAFE_INTEGER,
                    "finite actual direct command and immutable input tuple");
            String name = command.executable().getFileName().toString().toLowerCase(Locale.ROOT);
            StrictJson.require(!Set.of("cmd.exe","powershell.exe","pwsh.exe").contains(name),"direct cold-stage program only");
            for (ExactRef input : immutableInputs) {
                String path = input.path().replace('\\','/').toLowerCase(Locale.ROOT);
                StrictJson.require(!path.endsWith("/driver-state.json") && !path.endsWith(".ck3") && !path.endsWith(".sav"),
                        "stage source pins cannot cause persistence body reads");
            }
        }
        ObjectNode toJson() {
            ObjectNode value = StrictJson.object(); value.put("executable",command.executable().toString());
            var args = value.putArray("arguments"); command.arguments().forEach(args::add);
            value.put("cwd",command.cwd().toString()); value.put("stdout",command.stdout().toString());
            value.put("stderr",command.stderr().toString()); value.put("memory_limit_bytes",command.memoryLimitBytes());
            var environment = StrictJson.object(); command.environment().forEach(environment::put);
            value.put("environment_sha256",RecoveryEvidence.sha256(StrictJson.canonical(environment,LIMIT)));
            var names=value.putArray("environment_names"); command.environment().keySet().stream().sorted().forEach(names::add);
            value.set("executable_ref",executable.toJson()); var inputs = value.putArray("immutable_inputs");
            immutableInputs.forEach(ref -> inputs.add(ref.toJson())); value.put("deadline_utc",deadline.toString()); return value;
        }
    }
    private record Observed(ExactRef reference, FileStatIdentity identity, byte[] bytes) { }
    static final class Challenge {
        private final Thread owner = Thread.currentThread();
        private final ClosedInputsSessionAuthority authority;
        private final int preparedSequence;
        private final Stage stage;
        private final PlannedCommand command;
        private final ObjectNode value;
        private final Observed original;
        private final Path approval;
        private boolean reviewed;
        private Challenge(ClosedInputsSessionAuthority authority,int preparedSequence,Stage stage,PlannedCommand command,
                ObjectNode value,Observed original,Path approval) {
            this.authority=authority; this.preparedSequence=preparedSequence; this.stage=stage; this.command=command;
            this.value=value.deepCopy(); this.original=original; this.approval=approval;
        }
        ExactRef reference() { requireThread(); return original.reference(); }
        Path approvalPath() { requireThread(); return approval; }
        void requireCurrent() throws IOException {
            requireThread(); authority.requireNativeOwnerInputs(preparedSequence);
            StrictJson.require(Instant.now().isBefore(command.deadline()),"original independent stage challenge deadline");
            same(original,read(Path.of(original.reference().path())));
        }
        private void requireThread() { StrictJson.require(Thread.currentThread()==owner,"same actual Root stage challenge thread"); }
    }
    /** No public constructor, parser or boolean can make a reviewed stage. */
    static final class Reviewed {
        private final Challenge challenge;
        private final Observed approval;
        private boolean consumed;
        private Reviewed(Challenge challenge,Observed approval) { this.challenge=challenge; this.approval=approval; }
        Stage stage() { return challenge.stage; }
        PlannedCommand command() { return challenge.command; }
        ExactRef approvalRef() { return approval.reference(); }
        Instant reviewedAt() { return Instant.parse(StrictJson.text(StrictJson.parse(approval.bytes(),LIMIT).get("reviewed_at_utc"))); }
        void requireCurrent() throws IOException {
            challenge.requireCurrent(); same(approval,read(Path.of(approval.reference().path())));
        }
        void consumeImmediatelyBeforeSubmission() throws IOException {
            requireCurrent(); StrictJson.require(!consumed,"one independent Root stage approval, UNKNOWN is never replayed"); consumed=true;
        }
        boolean consumed() { return consumed; }
    }
    private RootColdStageReview() { }
    static Challenge create(ClosedInputsSessionAuthority authority,int preparedSequence,Path ownedDirectory,
            String rootSessionNonce,Stage stage,PlannedCommand command,
            Optional<WindowsJobProcess.ProcessIdentity> actualHeldGame) throws IOException {
        var inputs=authority.nativeRestoreInputs(preparedSequence);
        StrictJson.require(rootSessionNonce.matches("[0-9a-f]{32}") && !command.deadline().isAfter(authority.deadline())
                && Instant.now().isBefore(command.deadline()) && ownedDirectory.isAbsolute()
                && ownedDirectory.normalize().equals(ownedDirectory)
                && Files.isDirectory(ownedDirectory,LinkOption.NOFOLLOW_LINKS),"actual owned Root stage directory and finite original session");
        StrictJson.require((stage==Stage.SAVED_GAME_CREATE)==actualHeldGame.isEmpty(),"Game CREATE has no prior Game; later stages bind the actual held generation");
        ObjectNode value=StrictJson.object(); value.put("schema","xar.root-saved-cold-stage-challenge/v1");
        value.put("machine_id",authority.machineId()); value.put("session_nonce",rootSessionNonce);
        value.put("challenge_nonce",UUID.randomUUID().toString().replace("-","")); value.put("stage",stage.name());
        value.put("prepared_sequence",preparedSequence); value.put("created_at_utc",Instant.now().toString());
        value.put("deadline_utc",command.deadline().toString()); value.set("basis_ref",inputs.basis().reference().toJson());
        value.set("qualification_ref",inputs.qualificationRef().toJson()); value.set("committed_head_ref",inputs.committedHeadRef().toJson());
        value.set("plan_ref",inputs.plan().toJson()); value.set("quote_ref",inputs.quote().toJson()); value.set("preflight_ref",inputs.preflight().toJson());
        var effects=value.putArray("admitted_effects"); effects(stage).forEach(effect->effects.add(effect.name()));
        ObjectNode binding=command.toJson(); value.set("command",binding);
        value.put("binding_sha256",RecoveryEvidence.sha256(bindingBytes(command)));
        if (actualHeldGame.isPresent()) {
            var identity=actualHeldGame.orElseThrow(); ObjectNode game=value.putObject("actual_held_game");
            game.put("pid",identity.pid()); game.put("creation_filetime_decimal",identity.creationFiletimeDecimal());
            game.put("executable",identity.executable());
        } else { value.putNull("actual_held_game"); }
        String stem=stage.name().toLowerCase(Locale.ROOT)+"-"+value.get("challenge_nonce").textValue();
        Path path=ownedDirectory.resolve(stem+".challenge.json"),approval=ownedDirectory.resolve(stem+".root-review.json");
        Files.write(path,StrictJson.canonical(value,LIMIT),StandardOpenOption.CREATE_NEW);
        Challenge result=new Challenge(authority,preparedSequence,stage,command,value,read(path),approval);
        result.requireCurrent(); return result;
    }
    private static List<Effect> effects(Stage stage) {
        var common=List.of(Effect.KEEP_ORIGINAL_BASIS_CHECKPOINT_AND_EPISODE,Effect.UNKNOWN_NEVER_REPLAY,Effect.NO_WARM_OR_BUSINESS_GRANT);
        var effects=new java.util.ArrayList<>(switch(stage) {
            case SAVED_GAME_CREATE -> List.of(Effect.ARCHIVE_THREE_ORIGINAL_ENGINE_LOGS,Effect.CREATE_ORIGINAL_GAME_ONCE,Effect.LOAD_EXISTING_CHECKPOINT);
            case MCP_OWNER -> List.of(Effect.START_ORIGINAL_MCP_OWNER_ONCE,Effect.ORIGINAL_DRIVER_CONSTRUCTOR_AND_SOURCE_READS);
            case MOD_ABSENCE_ROOT_REVIEW -> List.of(Effect.INDEPENDENT_ROOT_CONFIRMS_KNOWN_EMPTY_MODS_FROM_EXACT_PROFILE_AND_STARTUP_SNAPSHOT);
            case INJECT -> List.of(Effect.LOAD_HELD_DLL_AND_DELIVER_NATIVE_HELLO,Effect.HELLO_MAY_READ_OR_REPLACE_DRIVER_AND_WAL,
                    Effect.HELLO_MAY_UPDATE_JOURNAL_OR_REMOVE_MANAGED_RESTORE_MARKER);
            case RAW_PREFLIGHT -> List.of(Effect.ONE_BOOTSTRAP_CAP_MAY_PERSIST_DRIVER);
            case CAPABILITIES_POSTSTATE -> List.of(Effect.VERIFY_ACTUAL_CURRENT_GAME_HEADER_AFTER_COMPLETED_CAP);
        });
        effects.addAll(common); return List.copyOf(effects);
    }
    static Optional<Reviewed> poll(Challenge challenge) throws IOException {
        challenge.requireCurrent(); StrictJson.require(!challenge.reviewed,"stage challenge review may be consumed once");
        if (!Files.exists(challenge.approval,LinkOption.NOFOLLOW_LINKS)) { return Optional.empty(); }
        Observed actual=read(challenge.approval); ObjectNode review=(ObjectNode)StrictJson.parse(actual.bytes(),LIMIT);
        validateReview(challenge.value,challenge.original.reference(),review,Instant.now());
        challenge.reviewed=true; return Optional.of(new Reviewed(challenge,actual));
    }
    static byte[] bindingBytes(PlannedCommand command) { return StrictJson.canonical(command.toJson(),LIMIT); }
    /** Pure boundary used by poll; this method never mints a Reviewed resource. */
    static void validateReview(ObjectNode challenge,ExactRef challengeRef,ObjectNode review,Instant now) {
        StrictJson.object(review,Set.of("schema","machine_id","reviewer","status","stage","session_nonce","challenge_nonce",
                "challenge_ref","binding_sha256","reviewed_at_utc","deadline_utc"));
        StrictJson.require("xar.root-saved-cold-stage-review/v1".equals(StrictJson.text(review.get("schema")))
                && "/root".equals(StrictJson.text(review.get("reviewer")))
                && "APPROVED_STAGE_ONCE".equals(StrictJson.text(review.get("status")))
                && challengeRef.equals(ExactRef.fromJson(review.get("challenge_ref"))),"independent actual Root review of this exact complete challenge");
        for (String field : List.of("machine_id","stage","session_nonce","challenge_nonce","binding_sha256","deadline_utc")) {
            StrictJson.require(StrictJson.text(review.get(field)).equals(StrictJson.text(challenge.get(field))),"same live Root stage review field: "+field);
        }
        Instant created=Instant.parse(StrictJson.utc(StrictJson.text(challenge.get("created_at_utc"))));
        Instant reviewed=Instant.parse(StrictJson.utc(StrictJson.text(review.get("reviewed_at_utc"))));
        Instant deadline=Instant.parse(StrictJson.utc(StrictJson.text(review.get("deadline_utc"))));
        StrictJson.require(!reviewed.isBefore(created) && !reviewed.isAfter(now) && now.isBefore(deadline),"new independent actual Root review within its original finite challenge");
    }
    private static Observed read(Path path) throws IOException {
        var identities=new WindowsSavedProofIdentityReader(); var before=identities.stat(path);
        StrictJson.require(before.bytes().signum()>0 && before.bytes().longValueExact()<=LIMIT,"bounded complete stage metadata");
        byte[] bytes; try(var input=Files.newInputStream(path)) { bytes=input.readNBytes(LIMIT+1); }
        StrictJson.require(bytes.length==before.bytes().longValueExact() && before.equals(identities.stat(path)),"unchanged native stage metadata identity");
        StrictJson.require(StrictJson.parse(bytes,LIMIT).isObject(),"complete stage metadata object");
        return new Observed(new ExactRef(path.toString(),bytes.length,RecoveryEvidence.sha256(bytes)),before,bytes);
    }
    private static void same(Observed original,Observed actual) {
        StrictJson.require(original.reference().equals(actual.reference()) && original.identity().equals(actual.identity())
                && java.util.Arrays.equals(original.bytes(),actual.bytes()),"original independent Root stage review bytes and native identity");
    }
}
