"""Read exact inputs once, qualify RAM output, and seal only small evidence."""
import json
import prepare_candidate as prepare
from test_wait_progress import cases


if __name__ == "__main__":
    print(json.dumps(cases(prepare.read_inputs()), indent=2), flush=True)
