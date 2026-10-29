package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.effects.NativeRegularMaaSubmission;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;

/** Fixed pre-Managed definition for the existing private native regular personal Create command.
 * A permission definition is not exact-build qualification, dispatch authority or created/payment evidence.
 */
public final class RegularMaaPrivatePermission {
    private RegularMaaPrivatePermission() { }
    public static final String PERMISSION="source_qualified_regular_maa_create_private_v1";
    public record Sources(ExactRef pythonProducer,ExactRef nativeMailbox,ExactRef nativeCreate,ExactRef nativeBuild4Binding) {
        public Sources {
            for(var source:List.of(pythonProducer,nativeMailbox,nativeCreate,nativeBuild4Binding))
                StrictJson.require(source!=null&&source.bytes()>0,"complete actual regular MAA producer sources required");
        }
        public List<ExactRef> all(){return List.of(pythonProducer,nativeMailbox,nativeCreate,nativeBuild4Binding);}
    }
    public static NativePrivateActionPermission permission(Sources sources,NativePrivateActionPermission.QualificationVerifier actual) {
        Objects.requireNonNull(sources);Objects.requireNonNull(actual);
        return new NativePrivateActionPermission(new OperationKey(NativeRegularMaaSubmission.STEP),PERMISSION,sources.nativeMailbox(),
                request->{verifySources(sources);validate(request);},(config,hello,guard,request)->{
                    verifySources(sources);
                    StrictJson.require(config.expectedGameSha256().equalsIgnoreCase(hello.gameSha256())&&guard.operation().value().equals(NativeRegularMaaSubmission.STEP)
                            &&hello.buildMatch()&&hello.adapterStatus().equals("ready")
                            &&Set.of("94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518").contains(hello.gameSha256().toUpperCase(java.util.Locale.ROOT)),"actual MAA native provider requires its exact qualified .3/.4 executable");
                    StrictJson.require(guard.observed().frame().identity().player().equals(BigInteger.valueOf(29829)),"actual native Create provider only supports current Robert29829");
                    var fields=StrictJson.parse(request.additionalFields().bytes());
                    StrictJson.require(StrictJson.integer(fields.get("expected_snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(guard.observed().frame().identity().nativeRevision())
                            &&StrictJson.integer(fields.get("expected_public_revision"),BigInteger.ONE,StrictJson.UINT64_MAX).equals(guard.observed().frame().revision())
                            &&BigInteger.valueOf(StrictJson.integer(fields.get("expected_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE)).equals(guard.observed().frame().identity().dateRaw()),"MAA private permission crossed its actual guard frame");
                    return actual.verify(config,hello,guard,request);
                });
    }
    public static void validate(NativeRequest request) { NativeRegularMaaSubmission.validateRequest(request); }
    private static void verifySources(Sources sources)throws IOException {
        for(ExactRef source:sources.all()) {
            var witness=SharedSourceFiles.observe(Path.of(source.path()));
            if(witness.source().bytes()!=source.bytes()||!witness.source().sha256().equals(source.sha256()))throw new IOException("regular MAA original producer source changed");
            SharedSourceFiles.assertUnchanged(witness);
        }
    }
}
