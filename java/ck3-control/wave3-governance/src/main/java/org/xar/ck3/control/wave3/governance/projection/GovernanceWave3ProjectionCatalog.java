package org.xar.ck3.control.wave3.governance.projection;

import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldown;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTermsCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryCodec;
import org.xar.ck3.control.wave3.governance.focusread.FocusReadProjectionPort;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistoryProjectionPort;
import org.xar.ck3.control.wave3.governance.lifestylescope.LifestyleScopeCodec;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderProjectionPort;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsProjectionPort;

/** Existing pure domains registered in the single host; source validation and serialization remain separate phases. */
public final class GovernanceWave3ProjectionCatalog implements ProjectionPortCatalog {
    public GovernanceWave3ProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(
                RegisteredProjection.of(new JsonPort(ProjectionOperation.GOVERNANCE_GOVERNMENT_QUERY_PREPARE, GovernmentQueryCodec::prepareProjection)),
                RegisteredProjection.of(new JsonPort(ProjectionOperation.GOVERNANCE_GOVERNMENT_QUERY_CONSUME, GovernmentQueryCodec::consumeProjection)),
                RegisteredProjection.of(new JsonPort(ProjectionOperation.GOVERNANCE_GOVERNMENT_QUERY_VALIDATE_RESPONSE, GovernmentQueryCodec::validateResponseProjection)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_DURATION_SCALE,
                        CrownCooldownCodec::decodeLiteral,
                        (CrownCooldownCodec.LiteralRequest input) -> CrownCooldown.scale(input.tokenId(), input.literalI32()),
                        CrownCooldownCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_CLOCK_INTERPRET,
                        CrownCooldownCodec::decodeClock,
                        (CrownCooldownCodec.ClockRequest input) -> CrownCooldown.interpret(input.observation(), input.dateRaw(), input.turnTick()),
                        CrownCooldownCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_NORMALIZED_CLOCK_INTERPRET,
                        CrownCooldownCodec::decodeNormalizedClock,
                        (CrownCooldownCodec.ClockRequest input) -> CrownCooldown.interpretNormalized(input.observation(), input.dateRaw()),
                        CrownCooldownCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_RAW_NORMALIZE,
                        CrownCooldownCodec::decodeRawNormalization, CrownCooldownCodec::normalizeRaw, CrownCooldownCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_TURN_TICK_NORMALIZE,
                        CrownCooldownCodec::decodeTickNormalization, CrownCooldownCodec::normalizeTurnTick, CrownCooldownCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_RETRY_MATCH,
                        CrownRetryCodec::decodeMatch, CrownRetryCodec::projectMatch, CrownRetryCodec::encodeMatch)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_RETRY_HORIZON,
                        CrownRetryCodec::decodeHorizon, CrownRetryCodec::projectHorizon, CrownRetryCodec::encodeHorizon)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_FINAL_TERMS_NORMALIZE,
                        CrownFinalTermsCodec::decode, (CrownFinalTerms.Payload input) -> input, CrownFinalTermsCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_FINAL_TERMS_PREPARE,
                        CrownFinalTermsCodec::decodePrepare, CrownFinalTermsCodec::projectPrepare, CrownFinalTermsCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_FINAL_TERMS_CONSUME,
                        CrownFinalTermsCodec::decodeReadback, (CrownFinalTerms.Readback input) -> input, CrownFinalTermsCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_CROWN_FINAL_TERMS_VALIDATE_RESPONSE,
                        CrownFinalTermsCodec::decodeResponseValidation, (CrownFinalTermsCodec.ResponseValidation input) -> input, CrownFinalTermsCodec::encode)),
                RegisteredProjection.of(new LifestyleHistoryProjectionPort()),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_LIFESTYLE_SCOPE,
                        LifestyleScopeCodec::decode, LifestyleScopeCodec::project, LifestyleScopeCodec::encodeResult)),
                RegisteredProjection.of(new FocusReadProjectionPort()),
                RegisteredProjection.of(new EducationProviderProjectionPort()),
                RegisteredProjection.of(new EducationOptionsProjectionPort()));
    }

    private record TypedPort<I, O>(ProjectionOperation operation, Function<byte[], I> decoder,
            Function<I, O> application, Function<O, byte[]> encoder) implements ProjectionPort<I, O> {
        private TypedPort {
            Objects.requireNonNull(operation); Objects.requireNonNull(decoder);
            Objects.requireNonNull(application); Objects.requireNonNull(encoder);
        }
        @Override public I decode(byte[] rawPayload) { return decoder.apply(rawPayload); }
        @Override public O project(I input) { return application.apply(input); }
        @Override public byte[] encode(O output) { return encoder.apply(output); }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
    /** Only the query adapter retains a byte-codec boundary, whose source validators emit explicit typed rejections. */
    private record JsonPort(ProjectionOperation operation, UnaryOperator<byte[]> application)
            implements ProjectionPort<ProjectionJson, ProjectionJson> {
        private JsonPort { Objects.requireNonNull(operation); Objects.requireNonNull(application); }
        @Override public ProjectionJson decode(byte[] rawPayload) { return ProjectionJson.object(rawPayload, inputMaximumBytes()); }
        @Override public ProjectionJson project(ProjectionJson input) { return ProjectionJson.value(application.apply(input.bytes()), outputMaximumBytes()); }
        @Override public byte[] encode(ProjectionJson output) { return output.bytes(); }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
}
