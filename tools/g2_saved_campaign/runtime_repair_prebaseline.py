"""A not-yet-created gameplay baseline is unknown rather than a Game fault."""
from pathlib import Path

from .runtime_repair_current_fault_guard import CurrentFaultPublisher
from . import runtime_repair_recording_guard as recording


class PrebaselinePublisher(CurrentFaultPublisher):
    def prebaseline_unknown(self):
        if (self.queue/'ROOT-CUMULATIVE-LOOP-STATE.json').is_file():
            self._real_loop_observed = True
            return False
        if getattr(self, '_real_loop_observed', False):
            return False
        return not any((self.queue/name).exists() for name in (
            'ROOT-CLEAN-CAMPAIGN-VERIFIED.json', 'ROOT-COLD-CAMPAIGN-VERIFIED.json',
            'ROOT-'+self.prefix.upper()+'-CAMPAIGN-VERIFIED.json'))

    def small_inputs(self):
        loop_path = self.queue/'ROOT-CUMULATIVE-LOOP-STATE.json'
        try:
            result = super().small_inputs()
        except FileNotFoundError as error:
            if (error.filename is None or Path(error.filename).resolve() != loop_path.resolve()
                    or not self.prebaseline_unknown()):
                raise
            feeder_path = self.session/('ROOT-CONTINUOUS-FEEDER-STATUS-'+self.prefix.upper()+'.json')
            feeder = recording.shared(feeder_path) if feeder_path.is_file() else {}
            return {}, feeder, loop_path, feeder_path
        self._real_loop_observed = True
        return result

    def observe_recording_pause(self):
        if self.prebaseline_unknown():
            return None
        return super().observe_recording_pause()
