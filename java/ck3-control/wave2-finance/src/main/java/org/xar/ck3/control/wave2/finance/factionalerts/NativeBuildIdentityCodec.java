package org.xar.ck3.control.wave2.finance.factionalerts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Shared original private_native_build_identity selector; this is not current native qualification. */
public final class NativeBuildIdentityCodec {
    private NativeBuildIdentityCodec() { }
    public static FactionAlertModel.Build fromSemanticSnapshot(JsonNode snapshot) {
        StrictJson.require(snapshot instanceof ObjectNode, "semantic snapshot object required");
        JsonNode diagnostics = snapshot.get("diagnostics");
        JsonNode hello = diagnostics != null && diagnostics.isObject() ? diagnostics.get("hello") : null;
        // Archived pre-HELLO 1.19 inputs retain their original identity branch; no modern identity is inferred.
        if (!(hello instanceof ObjectNode object)) return FactionAlertModel.Build.CK3_11906;
        JsonNode version = object.has("expected_ck3_version") ? object.get("expected_ck3_version") : object.get("game_version");
        JsonNode sha = object.has("expected_ck3_sha256") ? object.get("expected_ck3_sha256") : object.get("executable_sha256");
        try { return FactionAlertModel.Build.exact(StrictJson.text(version), StrictJson.text(sha)); }
        catch (ContractViolationException | ProjectionDomainRejection error) { throw new ContractViolationException("private nonwar source lacks a frozen exact native build", error); }
    }
}
