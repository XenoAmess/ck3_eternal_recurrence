"""Bounded synthetic integration of capture preparation, preservation and composition."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

from xar_promo.media import probe_and_write_bound_media
from xar_promo.pipeline import ProjectConfig
from xar_promo.process import CommandSpec, run_command
from xar_promo.render import execute_render_plan

import test_capture_media as fixture
from war_ai_promo import capture_media, composer, produce
from war_ai_promo.common import binding, load, write_new


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = None


class CaptureIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ARTIFACT_ROOT = ARTIFACT_ROOT / "fixture"
        fixture.ARTIFACT_ROOT.mkdir()
        fixture.CaptureMediaTests.setUpClass()
        cls.bundle = fixture.CaptureMediaTests.bundle
        cls.spec = fixture.CaptureMediaTests.spec
        cls.spec_path = ARTIFACT_ROOT / "capture-spec.json"
        write_new(cls.spec_path,{"schema":capture_media.SPEC_SCHEMA,"clips":[cls.spec]})
        cls.audio = ARTIFACT_ROOT / "synthetic-narration.wav"
        run_command(CommandSpec.create([
            "ffmpeg","-nostdin","-hide_banner","-loglevel","warning","-n",
            "-f","lavfi","-i","sine=frequency=660:sample_rate=48000:duration=0.5",
            "-c:a","pcm_s16le",cls.audio,
        ],label="synthetic narration placeholder, not TTS"),audit_directory=ARTIFACT_ROOT / "audio-command")
        row = {"id":"TEST-CUE","shot_id":"S30-24","chapter_id":"help",
               "claim_ids":["TEST-NOT-A-CLAIM"],"zh":"合成测试。","en":"Synthetic test.",
               "shot_title":"Synthetic only","speech_duration_seconds":0.5,"duration_seconds":0.8,
               "audio_artifact_id":"audio.TEST-CUE","audio":binding(cls.audio)}
        other = {**row,"id":"TEACH-CUE","audio_artifact_id":"audio.TEACH-CUE"}
        cls.inputs = {"media_scope":"teaching-graphics-radio-cut","provider":"synthetic-test",
                      "cues":[row,other],"human_signoff":"not-provided"}
        cls.config = ProjectConfig.from_mapping(load(ROOT / "promo/ck3_native_war_ai/promo-project.json"))

    def preserve_context(self, name):
        root = ARTIFACT_ROOT / name
        root.mkdir()
        artifacts = []
        def preserve(path, identifier, role, collection="raw"):
            # This fixture emulates the lifecycle seam only. The production
            # callback invokes actual xar-promo preserve; no test run is GREEN CK3.
            target = root / "preserved" / (identifier + Path(path).suffix)
            target.parent.mkdir(exist_ok=True)
            with Path(path).open("rb") as source, target.open("xb") as dest:
                shutil.copyfileobj(source,dest)
            artifacts.append(SimpleNamespace(artifact_id=identifier,path=target.relative_to(root).as_posix()))
        return root,artifacts,preserve

    def invocation(self, inputs, root, artifacts, preserve):
        selected = root / "selected-inputs.json"
        write_new(selected,inputs)
        preserve(selected,"production-inputs-v1","measured-production-inputs")
        for row in inputs["cues"]:
            preserve(self.audio,row["audio_artifact_id"],"narration-source")
        return composer.compose(self.config,SimpleNamespace(artifacts=artifacts),config_path=root / "config.json",
            run_path=root / "run-manifest.json",workdir=root / "build",
            adapter_factory=lambda:{"id":self.config.adapter},preset_factory=lambda:{"id":self.config.preset},
            validate_only=True)

    def test_mixed_prepare_preserve_and_real_subtitled_segment(self):
        root,artifacts,preserve = self.preserve_context("mixed-success")
        with patch.object(capture_media,"load_capture_bundle",return_value=self.bundle):
            selected = produce.prepare_captures(self.inputs,self.spec_path,root,preserve)
        self.assertEqual(selected["media_scope"],"mixed-footage")
        self.assertNotIn("capture_clip",self.inputs["cues"][0])
        mapped = selected["cues"][0]["capture_clip"]
        ids = {item.artifact_id for item in artifacts}
        self.assertIn(mapped["raw_artifact_id"],ids)
        self.assertIn(mapped["receipt_artifact_id"],ids)
        self.assertTrue(set(mapped["control_artifact_ids"]).issubset(ids))
        invoke = self.invocation(selected,root,artifacts,preserve)
        captured,teaching = invoke.draft.segments
        self.assertFalse(captured.visual_source.requires_resolution)
        self.assertTrue(teaching.visual_source.requires_resolution)
        self.assertTrue(captured.visual_source.path.is_relative_to(root / "preserved"))
        self.assertFalse((root / "build").exists(),"compose/plan must remain read-only")
        ass = root / "synthetic-captions.ass"
        ass.write_bytes(invoke.dependencies.subtitle_renderer(captured,None,workdir=root).encode("utf-8"))
        kwargs = dict(ffmpeg="ffmpeg",video_input=captured.visual_source.path,audio_input=captured.prepared_narration,
            partial_output=root / "segment.partial.mp4",final_output=root / "segment.mp4",
            audit_directory=root / "segment-audit",options=captured.render_options,ass_path=ass,
            working_directory=root)
        plan = invoke.dependencies.render_planner(**kwargs)
        argv = plan.commands[0].spec.argv
        graph = argv[argv.index("-filter_complex")+1]
        self.assertNotIn("tpad",graph)
        self.assertNotIn("fps=",graph)
        self.assertIn("ass=",graph)
        self.assertNotIn("-stream_loop",argv)
        self.assertIn("passthrough",argv)
        execute_render_plan(plan)
        probe = probe_and_write_bound_media("ffprobe",root / "segment.mp4",
            output_path=root / "segment.bound-probe.json",audit_directory=root / "segment-probe")
        self.assertAlmostEqual(probe.probe.require_duration(),0.8,places=2)
        self.assertEqual(len(probe.probe.audio_streams),1)
        capture_media._frame_audit("ffprobe",root / "segment.mp4",root / "segment-frames",24)
        # The unchanged teaching planner is selected by its different source.
        legacy = invoke.dependencies.render_planner(**{**kwargs,"video_input":root / "teaching.mp4"})
        legacy_graph = legacy.commands[0].spec.argv[legacy.commands[0].spec.argv.index("-filter_complex")+1]
        self.assertIn("tpad=stop_mode=clone",legacy_graph)
        write_new(root / "scope.json",{"synthetic_only":True,"rendered_seconds":0.8,
            "full_film_rendered":False,"ck3_started":False,"source_adapter_mocked":True,
            "lifecycle_preserve_fixture":True,"media":binding(root / "segment.mp4")})

    def test_duration_conflict_fails_after_preserving_evidence(self):
        root,artifacts,preserve = self.preserve_context("duration-conflict")
        inputs = deepcopy(self.inputs)
        inputs["cues"][0]["duration_seconds"] = 1.2
        with patch.object(capture_media,"load_capture_bundle",return_value=self.bundle):
            with self.assertRaisesRegex(ValueError,"duration conflict"):
                produce.prepare_captures(inputs,self.spec_path,root,preserve)
        self.assertTrue((root / "capture/001/integration-failure.json").exists())
        self.assertTrue((root / "capture/001/clip.mp4").exists())
        self.assertTrue(any(item.artifact_id.startswith("capture-raw-") for item in artifacts))
        self.assertTrue(any(item.artifact_id.startswith("capture-receipt-") for item in artifacts))
        self.assertFalse((root / "build").exists())

    def test_legacy_scope_remains_compatible_and_invalid_scope_rejected(self):
        root,artifacts,preserve = self.preserve_context("legacy")
        invocation = self.invocation(self.inputs,root,artifacts,preserve)
        self.assertTrue(all(row.visual_source.requires_resolution for row in invocation.draft.segments))
        badroot,badartifacts,badpreserve = self.preserve_context("bad-scope")
        with self.assertRaisesRegex(ValueError,"media_scope"):
            self.invocation({**self.inputs,"media_scope":"mixed-footage"},badroot,badartifacts,badpreserve)

    def test_unknown_cue_and_claim_fail_before_media_work(self):
        for key,value in [("cue_id","UNKNOWN"),("claim_ids",["UNBOUND"] )]:
            root,artifacts,preserve = self.preserve_context("bad-"+key)
            spec = ARTIFACT_ROOT / ("bad-"+key+".json")
            write_new(spec,{"schema":capture_media.SPEC_SCHEMA,"clips":[{**self.spec,key:value}]})
            with patch.object(produce,"prepare_capture_clip") as renderer, self.assertRaises(ValueError):
                produce.prepare_captures(self.inputs,spec,root,preserve)
            renderer.assert_not_called()
            self.assertFalse((root / "capture").exists())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root",type=Path,required=True)
    args = parser.parse_args()
    ARTIFACT_ROOT = args.artifact_root.resolve()
    ARTIFACT_ROOT.mkdir(parents=True,exist_ok=False)
    results = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CaptureIntegrationTests))
    write_new(ARTIFACT_ROOT / "result.json",{"schema":"ck3-war-ai.capture-integration-synthetic-check.v1",
        "result":"PASS" if results.wasSuccessful() else "FAIL","tests":results.testsRun,
        "failures":[{"test":str(test),"traceback":trace} for test,trace in results.failures],
        "errors":[{"test":str(test),"traceback":trace} for test,trace in results.errors],
        "synthetic_only":True,"full_film_rendered":False,"ck3_started":False,"upload_performed":False,
        "native_lifecycle_cli_run":False,"real_segment_rendered":True,"human_signoff":False})
    sys.exit(0 if results.wasSuccessful() else 1)
