package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave3.planning.m5peacetimeassembly.PeacetimeAssembly.obj;

import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;

/** One typed source -> actual intake -> original migrated opportunity-selector application. */
public final class PeacetimeAssemblyApplication {
    public static final String RESULT_SCHEMA = "xar.java.m5-peacetime-assembly-result.v1";
    public static final int MAXIMUM_BYTES = 131_072;
    private PeacetimeAssemblyApplication() { }

    public record Result(Obj sources, Obj intake) {
        public Result {
            Objects.requireNonNull(sources); Objects.requireNonNull(intake);
            require(new Text(PeacetimeAssembly.SOURCE_SCHEMA).equals(sources.get("schema")), "assembly source schema required");
            require(new Text(FormalProposalIntake.RESULT_SCHEMA).equals(intake.get("schema")), "actual intake schema required");
            require(sources.get("frame").equals(intake.get("frame")), "assembly intake crossed source frame");
            require(new Bool(false).equals(intake.get("formal_action_ready"))
                    && new Bool(false).equals(intake.get("resource_reservation_performed")), "pure intake cannot grant action or reservation credit");
        }
    }

    public static Result project(PeacetimeAssembly.Inputs input) {
        Objects.requireNonNull(input);
        Obj sources = PeacetimeAssembly.source(PeacetimeAssembly.compose(input));
        byte[] request = OpportunityJson.encode(obj("schema", new Text(FormalProposalIntake.REQUEST_SCHEMA),
                "snapshot", input.initialSnapshot(), "sources", sources));
        Obj intake = object(OpportunityJson.parse(FormalProposalIntake.collect(request)), "actual formal intake");
        return new Result(sources, intake);
    }

    public static byte[] encode(Result result) {
        Objects.requireNonNull(result);
        byte[] raw = OpportunityJson.encode(obj("schema", new Text(RESULT_SCHEMA), "sources", result.sources(), "intake", result.intake()));
        require(raw.length <= MAXIMUM_BYTES, "complete assembly/intake result exceeds registered 128 KiB role budget");
        return raw;
    }

    public static byte[] project(byte[] request) {
        return encode(project(PeacetimeAssemblyCodec.decode(request)));
    }
}
