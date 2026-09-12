"""Exercise runtime side-effect contracts in a fresh interpreter.

Native numerical worker threads and normal dependency caches are outside this
contract. Network, child processes, Python workers, and root logging setup are
unsolicited work for library import and ordinary estimation.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_import_and_estimation_do_not_start_external_work(tmp_path: Path) -> None:
    script = textwrap.dedent(
        """\
        import logging
        import sys
        import threading

        forbidden = []

        def audit(event, args):
            if event.startswith('socket.') or event in {
                'subprocess.Popen', 'os.system', 'os.fork', 'os.forkpty',
                'os.posix_spawn', 'os.exec', 'os.spawn',
            }:
                forbidden.append(event)
                raise AssertionError('Unexpected external operation: ' + event)

        def deny_thread(self, *args, **kwargs):
            forbidden.append('threading.Thread.start')
            raise AssertionError('Unexpected Python background worker')

        sys.addaudithook(audit)
        threading.Thread.start = deny_thread
        root = logging.getLogger()
        before_logging = (tuple(root.handlers), root.level, tuple(root.filters))

        import binspect
        import numpy as np

        x = np.linspace(-2.0, 2.0, 500)
        result = binspect.binscatter(x=x, y=x + np.sin(x), bins=5)
        assert result.n_obs == 500
        assert result.n_bins == 5
        assert 'matplotlib' not in sys.modules
        assert not forbidden, forbidden
        assert (tuple(root.handlers), root.level, tuple(root.filters)) == before_logging
        """
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
