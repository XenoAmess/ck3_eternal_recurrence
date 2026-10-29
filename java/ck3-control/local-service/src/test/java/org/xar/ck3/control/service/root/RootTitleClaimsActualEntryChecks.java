package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionTitleSelectorReads;
import org.xar.ck3.control.nativebridge.capabilities.interactions.TitleClaimsPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Whole-Root fixture continuation. Caller must supply a real privately assembled current Root; this helper mints none. */
public final class RootTitleClaimsActualEntryChecks {
    private RootTitleClaimsActualEntryChecks() { }
    public static RawJson exerciseActual(RootPublicHandlerProductsFactory.Context context,PublicBindings actualRegistry,
            PublicMethod method,TitleClaimsPublicCodec.Request currentRequest)throws IOException,InterruptedException {
        Objects.requireNonNull(context);Objects.requireNonNull(actualRegistry);Objects.requireNonNull(currentRequest);
        InteractionTitleSelectorReads.Kind expected=switch(method){
            case QUERY_TITLE_OWN_LAWS_V1->InteractionTitleSelectorReads.Kind.LAWS;
            case QUERY_PLAYER_CLAIMS_V1->InteractionTitleSelectorReads.Kind.CLAIMS;
            case QUERY_TITLE_HOLDER_V1->InteractionTitleSelectorReads.Kind.HOLDER;
            case QUERY_CURRENT_TITLE_APPOINTMENT_V1->InteractionTitleSelectorReads.Kind.APPOINTMENT;
            default->throw new IllegalArgumentException("one of the four actual original query routes required");
        };
        StrictJson.require(currentRequest.selector().kind()==expected&&actualRegistry.frozen(),"real final registry and matching current selector required");
        context.withCurrent(root->{var catalog=context.installed(root);var runtime=catalog.additionalDomains().driverRegistry().titleClaims();runtime.requireContext(catalog.context());runtime.requireOwner(root);return Boolean.TRUE;});
        var binding=actualRegistry.lookup(method).orElseThrow(()->new IOException("actual complete Root did not install the original title query"));
        var original=binding.invoke(PublicBindings.present(TitleClaimsPublicCodec.encode(currentRequest)));var output=StrictJson.parse(original.bytes());
        StrictJson.text(output.get("queried_snapshot_id"));StrictJson.require(output.get("queried_revision").isTextual()&&output.get("queried_native_revision").isTextual(),"actual public source projection lost decimal revisions");
        return original;
    }
}
