# utils/logger.py
import logging
import sys

_ROOT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_BASE_NAME = "clovord"


def _ensure_root_handler() -> None:
  """
  Ensure exactly one StreamHandler on the root logger.
  Keeps logging consistent without importing utils.helpers.
  """
  root = logging.getLogger()
  if not root.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_ROOT_FORMAT))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def get_logger(suffix: str | None = None) -> logging.Logger:
    """
    Liefert einen Logger:
      - 'clovord'                (wenn suffix=None)
      - 'clovord.<suffix>'       (wenn suffix gesetzt ist)
    Der Logger propagiert nach oben (Root-Handler schreibt).
    """
    _ensure_root_handler()
    name = _BASE_NAME if not suffix else f"{_BASE_NAME}.{suffix}"
    lg = logging.getLogger(name)
    lg.setLevel(logging.INFO)
    lg.propagate = True
    return lg


logger = get_logger()
