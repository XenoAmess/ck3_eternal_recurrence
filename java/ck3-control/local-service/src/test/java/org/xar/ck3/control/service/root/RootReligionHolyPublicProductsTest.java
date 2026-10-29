package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionHolyUi.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.*;
import org.xar.ck3.control.platform.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract.*;

/** Future selected-graph regressions. Software preparation does not grant Native, Root installation or Game admission. */
final class RootReligionHolyPublicProductsTest {
 @TempDir Path temporary;
 private static String requiredProperty(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_INPUT: "+name);return value;}
 private static ExactRef actualSource()throws IOException{String configured=requiredProperty("xar.religion.holy.root.source.path");var observed=SharedSourceFiles.observe(Path.of(configured));assertEquals("RootReligionHolyPublicProducts.java",Path.of(observed.source().path()).getFileName().toString());assertEquals(Long.parseLong(requiredProperty("xar.religion.holy.root.source.bytes")),observed.source().bytes());assertEquals(requiredProperty("xar.religion.holy.root.source.sha256"),observed.source().sha256());SharedSourceFiles.assertUnchanged(observed);return new ExactRef(observed.source().path(),observed.source().bytes(),observed.source().sha256());}
 private static ObjectNode arguments(String name){ObjectNode n=StrictJson.object();if(!name.equals(RootReligionHolyPublicProducts.KNOWLEDGE))n.put("expected_revision","18446744073709551615");var method=ReligionCodec.method(name);for(Field f:method.required())if(f!=Field.EXPECTED_REVISION)switch(f){case ACTION->n.put(f.wire(),"adopt");case HOLY_SITE_ID,BARONY_TITLE_ID->n.put(f.wire(),4294967294L);case TYPE_KEY->n.put(f.wire(),"holy_site_christian");case EXPECTED_PREVIEW_IDENTITY_SHA256->n.put(f.wire(),"a".repeat(64));default->throw new AssertionError("new required original Holy field needs a meaningful fixture: "+f);}return n;}
 private static PublicMcpDirectory.ToolCall call(String name,ObjectNode args){return new PublicMcpDirectory.ToolCall(name,new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(ReligionCodec.raw(args))),Optional.empty(),new McpCancellation());}
 @Test void originalTwelveDescriptorsEnterTheOneProductionTableWithExactSelectorsAndTypedSerde()throws Exception{
  var descriptors=RootOriginalPublicTestInputs.tools();var called=new ArrayList<String>();var bindings=RootReligionHolyPublicProducts.bindings(actualSource(),request->{called.add(request.method().name());if(request.method().name().equals(RootReligionHolyPublicProducts.KNOWLEDGE))return RootReligionHolyPublicProducts.knowledge(request);if(!request.method().name().startsWith("ck3_query_"))ReligionHolyUi.selection(request);throw new BeforeRoot();});
  assertEquals(12,bindings.size());assertEquals(Set.copyOf(RootReligionHolyPublicProducts.METHODS),bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(java.util.stream.Collectors.toSet()));
  for(var binding:bindings){var original=descriptors.stream().filter(v->v.name().equals(binding.name())).findFirst().orElseThrow(()->new AssertionError("actual original Holy descriptor absent: "+binding.name()));var c=call(binding.name(),arguments(binding.name()));RootPublicCatalogCodec.executableTool(original).validateArguments(c.arguments());exercise(binding,c);var request=ReligionCodec.decode(binding.name(),c.arguments().objectOrEmpty());assertEquals(request,ReligionCodec.decode(binding.name(),ReligionCodec.encode(request)));var extra=arguments(binding.name()).put("native_callback",1);assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(binding.name(),ReligionCodec.raw(extra)));}
  assertEquals(Set.copyOf(RootReligionHolyPublicProducts.METHODS),Set.copyOf(called));assertEquals(1,bindings.stream().filter(v->v.kind()==PublicMcpBindings.Kind.STATIC_KNOWLEDGE).count());
 }
 private static final class BeforeRoot extends RuntimeException{@java.io.Serial private static final long serialVersionUID=1L;}
 private static <Q,R> void exercise(McpExecutableDirectory.DirectBinding<Q,R> b,PublicMcpDirectory.ToolCall c)throws Exception{Q q=b.decoder().decode(c);if(b.name().equals(RootReligionHolyPublicProducts.KNOWLEDGE)){var result=b.encoder().encode(b.actual().invoke(q));assertNotNull(result);}else assertThrows(BeforeRoot.class,()->b.actual().invoke(q));}
 @Test void ninePublicMutationsContributeExactlySevenFiniteNavSelectorsAndNoParallelActionBinding()throws Exception{
  var selected=new HashSet<org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService.NavigationSelector>();int count=0;for(String name:RootReligionHolyPublicProducts.METHODS)if(!name.startsWith("ck3_query_")){Selection s=ReligionHolyUi.selection(ReligionCodec.decode(name,ReligionCodec.raw(arguments(name))));selected.add(new org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService.NavigationSelector(s.operation().window(),s.operation().wire()));count++;}assertEquals(9,count);assertEquals(RootReligionHolyPublicProducts.SELECTORS,selected);
  ExactRef source=actualSource();var provider=WindowsOriginalRuntimeHandoff.holyCreationOriginalOwnedLaunch(Optional.empty());var prepared=new RootReligionHolyPublicProducts.Prepared(new RootReligionHolyPublicProducts.Sources(source,source,source,new ReligionHolyReads.Sources(source,source,source),List.of(source),true,true,provider,RootReligionHolyPublicProducts.CreationAuthority.JAVA_MANAGED_SESSION,List.of(source)));
  assertTrue(prepared.domainRegistrations().isEmpty());assertTrue(prepared.privatePermissions().isEmpty());var nav=prepared.navigationDefinitions();assertEquals(1,nav.size());assertSame(nav,prepared.navigationDefinitions());assertEquals(selected,nav.getFirst().selectors());assertSame(source,nav.getFirst().source());assertTrue(nav.getFirst().permission().isEmpty());var metadata=nav.getFirst().controlMetadata().orElseThrow();assertEquals(RootReligionHolyPublicProducts.OBSERVER,metadata.observerSchema());assertEquals(5,metadata.controlSelectors().size());assertEquals(2,metadata.pendingSelectors().size());assertTrue(java.util.Collections.disjoint(metadata.controlSelectors(),metadata.pendingSelectors()));assertEquals(selected,java.util.stream.Stream.concat(metadata.controlSelectors().stream(),metadata.pendingSelectors().stream()).collect(java.util.stream.Collectors.toSet()));
  Set<String> artifactOnly=Set.of("select_relic_artifact","set_relic_slot","enshrine_relic","remove_relic","set_holy_site_creation_artifact_selection");assertTrue(selected.stream().noneMatch(v->artifactOnly.contains(v.operation())));
 }
 @Test void unchangedActualCommandFlowsThroughTheExistingRegistrationTypedProjectionBeforeAnyNativeWrite()throws Exception{
  ExactRef source=actualSource();var readSources=Arrays.stream(ReligionCapabilities.ReadKind.values()).map(k->new ReligionCapabilities.ReadSource(k,source)).toList();var actionSources=Arrays.stream(ReligionCapabilities.MutationSource.values()).map(k->new ReligionCapabilities.ActionSource(k,source)).toList();var seen=new AtomicReference<ActionCommand>();var kinds=new ArrayList<ReligionCapabilities.MutationKind>();var registration=new ReligionCapabilities.Registration(readSources,actionSources,List.of(),(kind,request)->{throw new AssertionError("no READ needed for pure native field preparation");},(kind,command)->{seen.set(command);kinds.add(kind);});
  try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("typed-original-preparation"),false)){ActionCommand base=fixture.command("holy-preparation-data");Frame frame=new Frame(base.before().frame().identity().nativeRevision(),base.before().frame().identity().dateRaw(),base.before().frame().identity().player(),BigInteger.valueOf(5));
   for(String name:RootReligionHolyPublicProducts.METHODS)if(!name.startsWith("ck3_query_")){Selection selection=ReligionHolyUi.selection(ReligionCodec.decode(name,ReligionCodec.raw(arguments(name))));ObjectNode fields=ReligionHolyUi.nativeFields(selection,frame);ObjectNode canonical=fields.deepCopy();canonical.putObject(RootReligionHolyPublicProducts.META).put("software_replay_metadata",true);var expected=new ExpectedPostcondition(1,base.before(),base.source(),RootReligionHolyPublicProducts.OBSERVER,List.of(new ExpectedBoolean(new FieldKey("holy.control_postcondition_observed"),true)));var command=new ActionCommand(base.actionId(),base.before(),base.source(),base.sessionId(),new OperationKey(ReligionCapabilities.NAVIGATE),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(canonical)),"software Holy canonical data"),expected,base.claims(),base.deadline());
    var request=registration.prepareNavigation(command,fields);assertSame(command,seen.get());assertEquals(ReligionCapabilities.NAVIGATE,request.step());assertEquals(Optional.of(ReligionCapabilities.NAVIGATE_CAPABILITY),request.requiredCapability());assertEquals(fields,ReligionCodec.object(request.additionalFields()));assertFalse(ReligionCodec.object(request.additionalFields()).has(RootReligionHolyPublicProducts.META));assertTrue(OpportunityJson.toNode(command.arguments()).has(RootReligionHolyPublicProducts.META));assertEquals(0,fixture.nativeActionWrites());
    assertThrows(IllegalArgumentException.class,()->registration.prepareNavigation(command,canonical));}
   assertEquals(9,kinds.size());assertTrue(kinds.contains(ReligionCapabilities.MutationKind.HOLY_SITE_CREATE_ONCE));assertTrue(kinds.contains(ReligionCapabilities.MutationKind.HOLY_SITE_CREATION_UI));assertTrue(kinds.contains(ReligionCapabilities.MutationKind.HOLY_SITE_UI));
  }
 }
 @Test void realPlatformMissingOriginalOwnedLaunchNeverEntersHolyCaptureOrClaimsAbsent()throws Exception{var calls=new AtomicInteger();var provider=WindowsOriginalRuntimeHandoff.holyCreationOriginalOwnedLaunch(Optional.empty());var result=provider.withOriginalStore(temporary.resolve("native-session/holy-site-creation-create-once-intents").toAbsolutePath().normalize(),"software-holy-test-machine",lease->{calls.incrementAndGet();return "unexpected";});assertInstanceOf(OriginalRuntimeHandoffProof.Unavailable.class,result);assertEquals(0,calls.get());assertFalse(java.nio.file.Files.exists(temporary.resolve("native-session")));}
 @Test void crossGenerationOnceIdentityRetainsPreviewActorDateEpisodeAndFiniteDecisionAliases(){Frame first=new Frame(BigInteger.valueOf(37),BigInteger.valueOf(51394920),BigInteger.valueOf(15893),BigInteger.valueOf(5));Frame later=new Frame(first.nativeRevision(),first.date(),first.actor(),new BigInteger("18446744073709551615"));var create=new Selection(Operation.CREATE,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.of("a".repeat(64)));String key=RootReligionHolyPublicProducts.onceKey("software-machine","episode-Σ-😀",create,first);assertEquals(key,RootReligionHolyPublicProducts.onceKey("software-machine","episode-Σ-😀",create,later));assertNotEquals(key,RootReligionHolyPublicProducts.onceKey("software-machine","episode-other",create,first));assertNotEquals(key,RootReligionHolyPublicProducts.onceKey("software-machine","episode-Σ-😀",new Selection(Operation.CREATE,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.of("b".repeat(64))),first));
  Selection legacy=new Selection(Operation.CONFIRM,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty()),generic=new Selection(Operation.CONFIRM,BigInteger.ZERO,Optional.empty(),Optional.of(ReligionModels.Decision.ADOPT),Optional.empty());assertEquals(RootReligionHolyPublicProducts.onceKey("software-machine","same",legacy,first),RootReligionHolyPublicProducts.onceKey("software-machine","same",generic,first));assertNotEquals(key,RootReligionHolyPublicProducts.onceKey("software-machine","episode-Σ-😀",create,new Frame(first.nativeRevision(),first.date().add(BigInteger.ONE),first.actor(),first.generation())));
 }
 @Test void onceKeyMatchesActualOriginalPythonIdentityAssignmentIncludingUnicodeEscapes()throws Exception{
  String repo=System.getProperty("xar.repository.root");if(repo==null||repo.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_RELIGION_REPOSITORY");Path source=Path.of(repo).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/holy_site_creation_create_once_private_transport.py");var pin=SharedSourceFiles.observe(source);SharedSourceFiles.assertUnchanged(pin);
  String program="""
import ast,hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(p.parents[2]))
from xar_autoplayer.bridge.version_identity import CK3_12004
tree=ast.parse(p.read_text(encoding='utf-8-sig'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='create_holy_site_once_private_v1')
identity=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='identity' for t in n.targets))
raw=json.load(sys.stdin)
env={'machine':raw['machine'],'CK3_12004':CK3_12004, '_scope':lambda before:raw['scope'], 'before':{'date_raw':raw['date'],'played_character':{'character_id':raw['actor']},'diagnostics':{'connection_generation':raw['generation']}}, 'OPERATION':'create_holy_site_once','KIND':'holy_site_creation','preview':raw['preview']}
exec(compile(ast.fix_missing_locations(ast.Module(body=[identity],type_ignores=[])),str(p),'exec'),env)
data={k:v for k,v in env['identity'].items() if k!='connection_generation'}
print(hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest())
""";
  Frame frame=new Frame(BigInteger.valueOf(37),BigInteger.valueOf(51394920),BigInteger.valueOf(15893),new BigInteger("18446744073709551615"));String episode="actual-software-Σ-😀";Selection create=new Selection(Operation.CREATE,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.of("a".repeat(64)));ObjectNode input=StrictJson.object().put("machine","software-machine").put("version",ReligionModels.Build.CROZIER4.version()).put("exe",ReligionModels.Build.CROZIER4.sha256()).put("date",frame.date()).put("actor",frame.actor()).put("generation",frame.generation()).put("preview",create.preview().orElseThrow());input.putObject("scope").put("kind","one_life_episode").put("episode_run_id",episode);
  var builder=new ProcessBuilder(requiredProperty("xar.python"),"-I","-B","-c",program,source.toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Path output=temporary.resolve("once-original.stdout"),error=temporary.resolve("once-original.stderr");builder.redirectOutput(output.toFile()).redirectError(error.toFile());var process=builder.start();try(var stdin=process.getOutputStream()){stdin.write(StrictJson.canonical(input));}assertTrue(process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS),"actual original Python identity oracle timeout");assertEquals(0,process.exitValue(),java.nio.file.Files.readString(error));assertEquals(RootReligionHolyPublicProducts.onceKey("software-machine",episode,create,frame),java.nio.file.Files.readString(output).strip());SharedSourceFiles.assertUnchanged(pin);
 }
}
