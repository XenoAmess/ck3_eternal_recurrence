package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import java.io.ByteArrayOutputStream;
import java.util.Arrays;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.combatroles.CombatRoles;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesCodec;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesPolicy;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;
import org.xar.ck3.control.wave2.military.commander.ArmyCommanderCandidatesCodec;
import org.xar.ck3.control.wave2.military.commander.CommanderQualityCodec;

/** Pure ports only. One military catalog supplies the centrally allocated operation identities. */
public final class CombatCommanderProjectionPorts {
    private static final JsonFactory TOKENS = new JsonFactory();
    // Registered projections use the transport budget; native full-frame commander reads keep their own limit.
    private static final int COMMANDER_PROJECTION_MAXIMUM_BYTES = ProjectionJson.MAX_BYTES;
    private CombatCommanderProjectionPorts() { }

    public record Operations(ProjectionOperation normalize, ProjectionOperation project,
            ProjectionOperation propose, ProjectionOperation admitObserved,
            ProjectionOperation plan, ProjectionOperation planNext) {
        public Operations {
            Objects.requireNonNull(normalize); Objects.requireNonNull(project); Objects.requireNonNull(propose);
            Objects.requireNonNull(admitObserved); Objects.requireNonNull(plan); Objects.requireNonNull(planNext);
            StrictJson.require(Set.of(normalize, project, propose, admitObserved, plan, planNext).size() == 6,
                    "combat/commander operations must be distinct central registrations");
        }
    }
    public static List<RegisteredProjection> registrations(Operations operations) {
        Objects.requireNonNull(operations);
        return List.of(RegisteredProjection.of(new Normalize(operations.normalize())),
                RegisteredProjection.of(new Project(operations.project())),
                RegisteredProjection.of(new Propose(operations.propose())),
                RegisteredProjection.of(new AdmitObserved(operations.admitObserved())),
                RegisteredProjection.of(new Plan(operations.plan(), false)),
                RegisteredProjection.of(new Plan(operations.planNext(), true)));
    }

    /** Wrapper keeps explicit null legal while RegisteredProjection requires a nonnull typed input. */
    public record Normalized(CombatRoles.Inputs value) { }
    public record ProjectInput(CombatRoles.Inputs value, ProjectionJson sourceProvenance) {
        public ProjectInput { Objects.requireNonNull(sourceProvenance); }
    }
    private record Normalize(ProjectionOperation operation) implements ProjectionPort<Normalized, Normalized> {
        @Override public int inputMaximumBytes() { return CombatRolesCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return CombatRolesCodec.MAX_BYTES; }
        @Override public Normalized decode(byte[] raw) {
            try {
                ObjectNode root = StrictJson.object(StrictJson.parse(raw, inputMaximumBytes()), Set.of("value"));
                return new Normalized(CombatRolesCodec.decode(root.get("value")));
            } catch (ContractViolationException error) { throw rejection(error); }
        }
        @Override public Normalized project(Normalized input) { return input; }
        @Override public byte[] encode(Normalized result) {
            ObjectNode root = StrictJson.object(); root.set("value", CombatRolesCodec.encode(result.value()));
            return StrictJson.canonical(root, outputMaximumBytes());
        }
    }
    private record Project(ProjectionOperation operation) implements ProjectionPort<ProjectInput, ProjectionJson> {
        @Override public int inputMaximumBytes() { return CombatRolesCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return CombatRolesCodec.MAX_BYTES; }
        @Override public ProjectInput decode(byte[] raw) {
            try {
                ObjectNode root = StrictJson.object(StrictJson.parse(raw, inputMaximumBytes()), Set.of("value", "source_provenance"));
                return new ProjectInput(CombatRolesCodec.decode(root.get("value")),
                        ProjectionJson.value(token(raw, "source_provenance"), inputMaximumBytes()));
            } catch (ContractViolationException error) { throw rejection(error); }
        }
        @Override public ProjectionJson project(ProjectInput input) {
            ObjectNode result = CombatRolesCodec.encodeProjection(CombatRolesPolicy.project(input.value(), null));
            result.remove("source_provenance");
            byte[] owned = StrictJson.canonical(result, outputMaximumBytes());
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            output.write(owned, 0, owned.length - 1);
            output.writeBytes(",\"source_provenance\":".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
            output.writeBytes(input.sourceProvenance().bytes()); output.write('}');
            return ProjectionJson.object(output.toByteArray(), outputMaximumBytes());
        }
        @Override public byte[] encode(ProjectionJson result) { return result.bytes(); }
    }
    public record CommanderInput(ProjectionJson value) {
        public CommanderInput { Objects.requireNonNull(value); }
    }
    private record Propose(ProjectionOperation operation)
            implements ProjectionPort<CommanderInput, CommanderQuality.Proposal> {
        @Override public int inputMaximumBytes() { return COMMANDER_PROJECTION_MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return COMMANDER_PROJECTION_MAXIMUM_BYTES; }
        @Override public CommanderInput decode(byte[] raw) {
            return new CommanderInput(ProjectionJson.object(raw, inputMaximumBytes()));
        }
        @Override public CommanderQuality.Proposal project(CommanderInput input) {
            return CommanderQualityCodec.decodeProposalInput(ArmyCommanderCandidatesCodec.parseJson(input.value().bytes()));
        }
        @Override public byte[] encode(CommanderQuality.Proposal result) {
            return ArmyCommanderCandidatesCodec.encodeJson(CommanderQualityCodec.encodeProposal(result));
        }
    }
    private record AdmitObserved(ProjectionOperation operation)
            implements ProjectionPort<CommanderInput, CommanderQuality.Proposal> {
        @Override public int inputMaximumBytes() { return COMMANDER_PROJECTION_MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return COMMANDER_PROJECTION_MAXIMUM_BYTES; }
        @Override public CommanderInput decode(byte[] raw) {
            return new CommanderInput(ProjectionJson.object(raw, inputMaximumBytes()));
        }
        @Override public CommanderQuality.Proposal project(CommanderInput input) {
            return CommanderQualityCodec.admitObservedQuery(input.value().bytes());
        }
        @Override public byte[] encode(CommanderQuality.Proposal result) {
            return ArmyCommanderCandidatesCodec.encodeJson(CommanderQualityCodec.encodeProposal(result));
        }
    }
    /** Validated JSON output of the existing codec; the original plan's extension fields retain decimals. */
    public record PlanResult(ProjectionJson value) {
        public PlanResult { Objects.requireNonNull(value); }
    }
    private record Plan(ProjectionOperation operation, boolean continuation) implements ProjectionPort<CommanderInput, PlanResult> {
        @Override public int inputMaximumBytes() { return COMMANDER_PROJECTION_MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return COMMANDER_PROJECTION_MAXIMUM_BYTES; }
        @Override public CommanderInput decode(byte[] raw) {
            return new CommanderInput(ProjectionJson.object(raw, inputMaximumBytes()));
        }
        @Override public PlanResult project(CommanderInput input) {
            byte[] raw = input.value().bytes();
            byte[] result = continuation ? CommanderQualityCodec.continuePlan(raw) : CommanderQualityCodec.plan(raw);
            return new PlanResult(ProjectionJson.object(result, outputMaximumBytes()));
        }
        @Override public byte[] encode(PlanResult result) { return result.value().bytes(); }
    }
    private static byte[] token(byte[] raw, String field) {
        try (JsonParser parser = TOKENS.createParser(raw)) {
            parser.nextToken();
            while (parser.nextToken() != com.fasterxml.jackson.core.JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken();
                int begin = Math.toIntExact(parser.currentTokenLocation().getByteOffset());
                parser.skipChildren(); parser.finishToken();
                int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                if (field.equals(name)) { return Arrays.copyOfRange(raw, begin, end); }
            }
            throw new IllegalArgumentException("required source token missing");
        } catch (IOException error) { throw new IllegalArgumentException("invalid source token", error); }
    }
    private static ProjectionDomainRejection rejection(IllegalArgumentException error) {
        return new ProjectionDomainRejection(Objects.requireNonNullElse(error.getMessage(), "domain input rejected"));
    }
}

