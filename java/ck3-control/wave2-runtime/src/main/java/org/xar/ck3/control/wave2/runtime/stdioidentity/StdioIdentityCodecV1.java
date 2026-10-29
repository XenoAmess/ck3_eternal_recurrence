package org.xar.ck3.control.wave2.runtime.stdioidentity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.stdioidentity.StdioIdentityPlanV1.SourcePinV1;

/** New versioned measurement-plan wire; never decodes a successful observation or ownership proof. */
public final class StdioIdentityCodecV1 {
    private static final Set<String> PLAN_FIELDS = Set.of("schema", "machine_id", "game", "queue", "app", "entry_sources");
    private static final Set<String> PROCESS_FIELDS = Set.of("pid", "creation_filetime_decimal", "executable");
    private static final Set<String> SOURCE_FIELDS = Set.of("path", "bytes", "sha256");

    private StdioIdentityCodecV1() { }

    public static StdioIdentityPlanV1 decode(byte[] raw) {
        ObjectNode input = StrictJson.object(StrictJson.parse(raw), PLAN_FIELDS);
        StrictJson.require(StdioIdentityPlanV1.SCHEMA.equals(StrictJson.text(input.get("schema"))),
                "exact stdio identity measurement-plan version required");
        JsonNode sources = input.get("entry_sources");
        StrictJson.require(sources.isArray() && !sources.isEmpty() && sources.size() <= StdioIdentityPlanV1.MAX_SOURCES,
                "one to eight frozen entry source pins required");
        List<SourcePinV1> pins = new ArrayList<>(sources.size());
        for (JsonNode value : sources) {
            ObjectNode source = StrictJson.object(value, SOURCE_FIELDS);
            pins.add(new SourcePinV1(path(source.get("path")), StrictJson.integer(source.get("bytes"),
                    0, StdioIdentityPlanV1.MAX_SOURCE_BYTES), StrictJson.text(source.get("sha256"))));
        }
        return new StdioIdentityPlanV1(StrictJson.text(input.get("machine_id")), process(input.get("game")),
                process(input.get("queue")), process(input.get("app")), pins);
    }

    public static byte[] encode(StdioIdentityPlanV1 plan) {
        StrictJson.require(plan != null, "validated identity measurement plan required");
        ObjectNode output = StrictJson.object();
        output.put("schema", StdioIdentityPlanV1.SCHEMA); output.put("machine_id", plan.machineId());
        output.set("game", process(plan.game())); output.set("queue", process(plan.queue()));
        output.set("app", process(plan.app()));
        ArrayNode sources = output.putArray("entry_sources");
        for (SourcePinV1 pin : plan.entrySources()) {
            ObjectNode source = sources.addObject();
            source.put("path", pin.path().toString()); source.put("bytes", pin.bytes()); source.put("sha256", pin.sha256());
        }
        return StrictJson.canonical(output);
    }

    private static ProcessIdentityClaimV1 process(JsonNode value) {
        ObjectNode process = StrictJson.object(value, PROCESS_FIELDS);
        return new ProcessIdentityClaimV1(StrictJson.integer(process.get("pid"), 1, 0xffff_ffffL),
                StrictJson.text(process.get("creation_filetime_decimal")), path(process.get("executable")));
    }

    private static ObjectNode process(ProcessIdentityClaimV1 value) {
        ObjectNode process = StrictJson.object(); process.put("pid", value.pid());
        process.put("creation_filetime_decimal", value.creationFiletimeDecimal());
        process.put("executable", value.executable().toString()); return process;
    }

    private static Path path(JsonNode value) {
        try { return Path.of(StrictJson.text(value)); }
        catch (InvalidPathException error) { throw new ContractViolationException("valid absolute path required", error); }
    }
}
