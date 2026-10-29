package org.xar.ck3.control.application.ritecreation;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.need;

/** One v2 canonical slot: original Java intentions and separately typed original Python intentions. */
public record RiteCreationDomainState(RiteCreationState.State javaState,Optional<RiteCreationLegacyStore.Imported> legacyStore,List<OpaqueOriginalCapture> unresolvedOpaqueOriginals){
    public static final String SCHEMA="xar.java.rite-creation-once/v2";
    public record OpaqueOriginalCapture(ExactRef originalManifest,String reason){public OpaqueOriginalCapture{Objects.requireNonNull(originalManifest);need(reason!=null&&!reason.isBlank()&&reason.length()<=1024,"bounded unresolved original-store diagnosis required");}}
    public RiteCreationDomainState{Objects.requireNonNull(javaState);Objects.requireNonNull(legacyStore);unresolvedOpaqueOriginals=List.copyOf(unresolvedOpaqueOriginals);need(unresolvedOpaqueOriginals.size()<=128,"bounded complete opaque original history required");}
    public RiteCreationDomainState(RiteCreationState.State actual,Optional<RiteCreationLegacyStore.Imported> legacy){this(actual,legacy,List.of());}
    public RiteCreationDomainState withJava(RiteCreationState.State actual){return new RiteCreationDomainState(actual,legacyStore,unresolvedOpaqueOriginals);}
    public RiteCreationDomainState imported(RiteCreationLegacyStore.Imported actual){return new RiteCreationDomainState(javaState,Optional.of(RiteCreationLegacyStore.merge(legacyStore,actual)),unresolvedOpaqueOriginals);}
    public RiteCreationDomainState quarantine(OpaqueOriginalCapture actual){var all=new ArrayList<>(unresolvedOpaqueOriginals);if(!all.contains(actual))all.add(actual);return new RiteCreationDomainState(javaState,legacyStore,all);}
    public Optional<RiteCreationLegacyStore.Intent> legacyBlocking(RiteCreationState.Key key){need(unresolvedOpaqueOriginals.isEmpty(),"unparseable original once history remains UNKNOWN; no new final confirmation");return legacyStore.orElseThrow(()->new IllegalArgumentException("original Python once store has no qualified custody import; final confirmation is read-only")).intents().stream().filter(v->v.blocksRetry()&&v.matches(key)).findFirst();}
    public RawJson encode(){ObjectNode n=empty().put("schema",SCHEMA);n.set("java_intentions_v1",object(RiteCreationState.encode(javaState)));if(legacyStore.isPresent())n.set("original_python_once_store_v1",RiteCreationLegacyStore.toJson(legacyStore.orElseThrow()));else n.putNull("original_python_once_store_v1");var rows=n.putArray("unresolved_opaque_originals");for(OpaqueOriginalCapture v:unresolvedOpaqueOriginals){ObjectNode row=empty().put("reason",v.reason());row.set("original_manifest",v.originalManifest().toJson());rows.add(row);}return raw(n);}
    public static RiteCreationDomainState decode(RawJson original){ObjectNode n=object(original);shape(n,Set.of("schema","java_intentions_v1","original_python_once_store_v1","unresolved_opaque_originals"),Set.of());equal(get(n,"schema"),SCHEMA);var rows=get(n,"unresolved_opaque_originals");need(rows.isArray()&&rows.size()<=128,"bounded unresolved original capture history required");var opaque=new ArrayList<OpaqueOriginalCapture>();for(var v:rows){ObjectNode row=object(v);shape(row,Set.of("original_manifest","reason"),Set.of());opaque.add(new OpaqueOriginalCapture(ExactRef.fromJson(get(row,"original_manifest")),text(get(row,"reason"))));}var result=new RiteCreationDomainState(RiteCreationState.decode(raw(get(n,"java_intentions_v1"))),nullable(n,"original_python_once_store_v1",RiteCreationLegacyStore::fromJson),opaque);need(result.encode().equals(original),"canonical full Rite v2 body representation changed");return result;}
    /** Original Java v1 has never been production-adopted. This is audit DATA only, not a live v2 import or empty-FS authority. */
    public static RiteCreationState.State auditOriginalJavaV1(RawJson actual){return RiteCreationState.decode(actual);}
}
