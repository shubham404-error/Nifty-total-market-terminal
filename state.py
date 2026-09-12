import streamlit as st
import pandas as pd
from constants import AI_STRATEGY_PREFILTER_SCORE, AI_DEFAULT_FINAL_BUY_CONVICTION, AI_DEFAULT_FINAL_BUY_LIQUIDITY

def _current_scan_id():
    """Stable identity for the current scan. Prevents stale strategy outputs."""
    existing = st.session_state.get("scan_id")
    if existing:
        return str(existing)
    from ui.components import get_snapshot
    import hashlib
    snapshot = get_snapshot()
    if isinstance(snapshot, pd.DataFrame) and not snapshot.empty:
        basis = snapshot[[c for c in ["Symbol", "Date", "Close"] if c in snapshot.columns]].copy()
        digest = hashlib.sha256(basis.to_csv(index=False).encode()).hexdigest()[:16]
        return f"scan-{digest}"
    return "no-scan"


def _invalidate_strategy_state(scan_id):
    """Drop all strategy/AI artifacts that belong to an older scan."""
    st.session_state["ai_strategy_registry"] = {}
    for key in [
        "ai_confluence_output", "ai_final_buy_output", "ai_emerging_working",
        "ai_emerging_buy_output", "ai_final_buy_cache", "ai_emerging_cache",
        "buy_fundamentals_cache", "emerging_fundamentals_cache",
    ]:
        st.session_state.pop(key, None)
    st.session_state["strategy_scan_id"] = scan_id


def _strategy_cache_valid(cache):
    return isinstance(cache, dict) and cache.get("scan_id") == _current_scan_id()


def _ai_register_strategy_output(strategy_name, frame, metadata=None):
    """Central, exact strategy registry for the AI layer."""
    if "ai_strategy_registry" not in st.session_state:
        st.session_state["ai_strategy_registry"] = {}

    st.session_state["ai_strategy_registry"][strategy_name] = {
        "frame": frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame(),
        "metadata": metadata or {},
    }


def _ensure_ai_strategy_outputs():
    """Self-sufficient AI strategy build for the current scan only."""
    scan_id=_current_scan_id()
    from ui.components import get_snapshot, get_convergence
    from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
    registry=st.session_state.get("ai_strategy_registry",{})
    if not isinstance(registry,dict) or st.session_state.get("strategy_scan_id")!=scan_id:
        _invalidate_strategy_state(scan_id)
        registry={}
    convergence = get_convergence()
    confluence=build_ai_confluence_pool(convergence)
    final=build_final_buy_list(convergence,AI_DEFAULT_FINAL_BUY_CONVICTION,AI_DEFAULT_FINAL_BUY_LIQUIDITY,prefilter_score=AI_STRATEGY_PREFILTER_SCORE)
    emerging=_build_emerging_scored(get_snapshot())
    emerging_buy=build_emerging_buy_list(emerging)
    _ai_register_strategy_output("confluence",confluence,{"minimum_score":AI_STRATEGY_PREFILTER_SCORE,"canonical_ai_pool":True,"scan_id":scan_id})
    _ai_register_strategy_output("final_buy_list",final,{"minimum_investor_conviction":AI_DEFAULT_FINAL_BUY_CONVICTION,"use_liquidity_filter":AI_DEFAULT_FINAL_BUY_LIQUIDITY,"prefilter_score":AI_STRATEGY_PREFILTER_SCORE,"canonical_ai_pool":True,"scan_id":scan_id})
    _ai_register_strategy_output("emerging_setups",emerging,{"scan_id":scan_id})
    _ai_register_strategy_output("emerging_buy_list",emerging_buy,{"scan_id":scan_id})
    st.session_state["ai_confluence_output"]=confluence.copy(); st.session_state["ai_final_buy_output"]=final.copy(); st.session_state["ai_emerging_working"]=emerging.copy(); st.session_state["ai_emerging_buy_output"]=emerging_buy.copy()


def _ai_registered_strategy_frame(strategy_name, legacy_key=None):
    registry = st.session_state.get("ai_strategy_registry", {})
    entry = registry.get(strategy_name, {}) if isinstance(registry, dict) else {}
    metadata = entry.get("metadata", {}) if isinstance(entry, dict) else {}
    frame = entry.get("frame") if isinstance(entry, dict) else None
    if metadata.get("scan_id") == _current_scan_id() and isinstance(frame, pd.DataFrame):
        return frame, metadata
    return None, {}


