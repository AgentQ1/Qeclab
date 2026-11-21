"""Decoder tiers. Each one is bound to a Problem and decodes one shot at a time.

Names (see build): the kit's baselines `bposd` and `relay`, plain min-sum `bp30` and `bp200`,
early-stopping relay-BP `fast` (tier 1) and `relay1`, and the large ensemble `strong` (tier 2).
A `+flags` suffix gives the tier the herald flags of each shot as per-shot priors.
"""
from dataclasses import dataclass

import numpy as np
import relay_bp
from ldpc import BpDecoder, BpOsdDecoder

from decoders import BPOSD_SETTINGS, RELAY_SETTINGS

from . import features

SETTINGS = {
    "relay": {},                                        # the kit's relay-BP: 5 solutions, up to 300 legs
    "relay1": {"stop_nconv": 1},                        # first solution, up to 300 legs
    "fast": {"stop_nconv": 1, "num_sets": 10},          # tier 1: first solution, give up after 10 legs
    "fast0": {"stop_nconv": 1, "num_sets": 0},          # first leg only (80 iterations of BP with memory)
    "strong": {"stop_nconv": 20, "num_sets": 600},      # tier 2: lightest of 20 solutions, up to 600 legs
    "strong10": {"stop_nconv": 10, "num_sets": 600},
}
BP_SETTINGS = {"bp30": {"max_iter": 30}, "bp200": {"max_iter": 200}}


@dataclass
class TierResult:
    error: np.ndarray                     # uint8, one entry per column of H
    converged: bool                       # the error explains the syndrome
    iterations: int                       # BP iterations used
    weight: float = 0.0                   # log-likelihood weight of the error under the priors used
    posterior: np.ndarray | None = None   # relay-BP only
    features: np.ndarray | None = None    # relay-BP tiers only


def llr(priors):
    """Log-likelihood weight of every mechanism: the cost of assuming it fired."""
    priors = np.clip(priors, 1e-12, 0.5 - 1e-9)
    return np.log((1 - priors) / priors)


class Tier:
    """Shared prior handling. Subclasses implement _set_priors and _decode."""
    has_features = False

    def __init__(self, problem, use_flags):
        self.problem = problem
        self.use_flags = bool(use_flags and problem.f)
        # Without flags a tier assumes the blind priors. With flags it gets priors per shot.
        self.weights = llr(problem.priors)

    def decode_shot(self, syndrome, other_weight=0, fired=()):
        herald_columns = ()
        if self.use_flags:
            priors = self.problem.shot_priors(fired)
            self._set_priors(priors)
            self.weights = llr(priors)
            herald_columns = self.problem.herald_columns(fired)
        result = self._decode(syndrome)
        result.weight = float(self.weights[result.error.astype(bool)].sum())
        if self.has_features:
            result.features = features.extract(syndrome, result, self.weights, self.problem, self.pre_iter, other_weight,
                                               fired if self.use_flags else (), herald_columns)
        return result


class RelayTier(Tier):
    has_features = True

    def __init__(self, problem, use_flags=False, **changes):
        super().__init__(problem, use_flags)
        self.settings = RELAY_SETTINGS | changes
        self.pre_iter = self.settings["pre_iter"]
        self.H = problem.H.tocsr()
        self._set_priors(problem.priors)

    def _set_priors(self, priors):
        # relay-bp has no call to change priors, so the decoder is rebuilt (about 3 ms).
        self.decoder = relay_bp.RelayDecoderF64(self.H, error_priors=np.asarray(priors, np.float64), **self.settings)

    def _decode(self, syndrome):
        out = self.decoder.decode_detailed(syndrome)
        return TierResult(np.asarray(out.decoding, np.uint8), bool(out.success), int(out.iterations),
                          posterior=np.asarray(out.posterior_ratios))


class BpOsdTier(Tier):
    def __init__(self, problem, use_flags=False, **changes):
        super().__init__(problem, use_flags)
        self.decoder = BpOsdDecoder(problem.H, error_channel=list(problem.priors), **(BPOSD_SETTINGS | changes))

    def _set_priors(self, priors):
        self.decoder.update_channel_probs(np.asarray(priors, np.float64))

    def _decode(self, syndrome):
        return TierResult(np.asarray(self.decoder.decode(syndrome), np.uint8), True, int(self.decoder.iter))


class BpTier(Tier):
    """Plain min-sum BP, the first stage of the team's hybrid_rule."""

    def __init__(self, problem, use_flags=False, **changes):
        super().__init__(problem, use_flags)
        settings = {"bp_method": "minimum_sum", "ms_scaling_factor": 1.0} | changes
        self.decoder = BpDecoder(problem.H, error_channel=list(problem.priors), **settings)

    def _set_priors(self, priors):
        self.decoder.update_channel_probs(np.asarray(priors, np.float64))

    def _decode(self, syndrome):
        error = np.asarray(self.decoder.decode(syndrome), np.uint8)
        return TierResult(error, bool(self.decoder.converge), int(self.decoder.iter))


def build(name, problem):
    """Tier by name, e.g. 'relay', 'fast+flags', 'bposd'."""
    kind, _, suffix = name.partition("+")
    if suffix not in ("", "flags"):
        raise ValueError(f"unknown tier {name}")
    use_flags = suffix == "flags"
    if kind == "bposd":
        return BpOsdTier(problem, use_flags)
    if kind in BP_SETTINGS:
        return BpTier(problem, use_flags, **BP_SETTINGS[kind])
    if kind in SETTINGS:
        return RelayTier(problem, use_flags, **SETTINGS[kind])
    raise ValueError(f"unknown tier {name}")
