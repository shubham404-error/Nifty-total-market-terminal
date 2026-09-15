import pandas as pd
import numpy as np
import streamlit as st
from engine import fundamental_snapshot, investor_quality_gate
from ui.components import get_convergence, get_snapshot

from decision_config import V4_CONFIG
from market_regime import update_market_regime
import datetime
from constants import (AI_STRATEGY_PREFILTER_SCORE, AI_DEFAULT_FINAL_BUY_CONVICTION,
                       AI_DEFAULT_FINAL_BUY_LIQUIDITY, AI_FUNDAMENTAL_FETCH_LIMIT,
                       STAGE_3_PENALTY_MULTIPLIER, FILTERS_SHADOW_MODE)


def _fundamental_for_scan(namespace, yahoo_symbol):
    from state import _current_scan_id
    scan_id = _current_scan_id()
    cache = st.session_state.setdefault(namespace, {})
    key = f"{scan_id}|{yahoo_symbol}"
    if key not in cache:
        try:
            result = fundamental_snapshot(yahoo_symbol)
            cache[key] = result if isinstance(result, dict) else {}
        except Exception:
            cache[key] = {}
    return cache[key]


def build_ai_confluence_pool(convergence=None, min_score=AI_STRATEGY_PREFILTER_SCORE):
    """Canonical AI Confluence pool using an explicit score threshold and active setups only."""
    if convergence is None:
        convergence = get_convergence()
    if not isinstance(convergence, pd.DataFrame) or convergence.empty:
        return pd.DataFrame()
    score = pd.to_numeric(convergence.get("ConvergenceScore"), errors="coerce")
    setup = convergence.get("Setup", pd.Series("No active setup", index=convergence.index))
    return convergence.loc[
        (score >= float(min_score))
        & setup.astype(str).ne("No active setup")
    ].copy().reset_index(drop=True)


def compute_funnel_booleans(snapshot: pd.DataFrame) -> pd.DataFrame:
    if snapshot.empty:
        return snapshot
        
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    index_stage = 2 # Dummy value if we don't have Nifty50. Ideally fetch from actual Nifty50 stage
    # For now, just use 2.
    
    # Check if Nifty 50 exists in snapshot to get actual stage
    nifty_row = snapshot[snapshot["Symbol"] == "^NSEI"]
    if not nifty_row.empty:
        index_stage = int(nifty_row["Stage"].iloc[0])
        
    regime_info = update_market_regime(date_str, snapshot, index_stage)
    regime = regime_info["Regime"]
    
    current_regime_threshold = V4_CONFIG["CONFLUENCE_STANDARD"]
    if regime == "DEFENSIVE":
        current_regime_threshold = V4_CONFIG["CONFLUENCE_DEFENSIVE"]
        
    snapshot["passed_data_quality"] = snapshot["HistoryEligible"].fillna(False).astype(bool)
    
    # 2. LIQUIDITY (Hard Gate)
    snapshot["passed_liquidity"] = pd.to_numeric(snapshot.get("AvgTradedValue20", 0), errors="coerce") >= 1_00_00_000
    
    # 3. STAGE (Hard Gate)
    snapshot["passed_stage"] = snapshot.get("Stage", -1).isin([1, 2])
    
    # 4. LEADERSHIP (Hard Gate)
    snapshot["passed_leadership"] = pd.to_numeric(snapshot.get("RS_Rating", 0), errors="coerce") >= V4_CONFIG["RS_RATING_MIN"]
    
    # 5. CONFLUENCE (Hard Gate)
    snapshot["passed_confluence"] = pd.to_numeric(snapshot.get("ConvergenceScore", 0), errors="coerce") >= current_regime_threshold
    
    # 6. ENTRY SETUP (Hard Gate)
    valid_patterns = V4_CONFIG["VALID_ENTRY_PATTERNS"]
    snapshot["passed_entry"] = snapshot.get("EntryPattern", "").isin(valid_patterns) & snapshot.get("EntrySetupQualified", False).astype(bool)
    
    # Overall funnel pass
    snapshot["passed_all"] = (
        snapshot["passed_data_quality"] & 
        snapshot["passed_liquidity"] & 
        snapshot["passed_stage"] & 
        snapshot["passed_leadership"] & 
        snapshot["passed_confluence"] & 
        snapshot["passed_entry"]
    )
    
    if regime == "CRISIS":
        snapshot["passed_all"] = False
        
    return snapshot

def build_final_buy_list(
    convergence=None,
    min_score=AI_DEFAULT_FINAL_BUY_CONVICTION,
    use_liquidity=AI_DEFAULT_FINAL_BUY_LIQUIDITY,
    prefilter_score=None,
):
    """Shared Final Buy List engine used by both the page and AI verification."""
    if convergence is None:
        convergence = get_convergence()
    if not isinstance(convergence, pd.DataFrame) or convergence.empty:
        return pd.DataFrame()

    source = convergence.copy()
    source = compute_funnel_booleans(source)
    if not FILTERS_SHADOW_MODE:
        source = source[source["passed_all"]].copy()
        
    if prefilter_score is not None:
        source = build_ai_confluence_pool(source, min_score=prefilter_score)

    technical = investor_quality_gate(source)
    if use_liquidity and not technical.empty:
        technical = technical.loc[technical["LiquidityEligible"].fillna(False)].copy()
    if technical.empty:
        return pd.DataFrame()

    finalists = technical.head(AI_FUNDAMENTAL_FETCH_LIMIT).copy()
    rows = []
    for _, row in finalists.iterrows():
        fund = _fundamental_for_scan("buy_fundamentals_cache", row.get("Yahoo Symbol"))
        market_cap = pd.to_numeric(fund.get("Market Cap"), errors="coerce")
        revenue_growth = pd.to_numeric(fund.get("Revenue Growth %"), errors="coerce")
        margin = pd.to_numeric(fund.get("Profit Margin %"), errors="coerce")
        debt_equity = pd.to_numeric(fund.get("Debt/Equity"), errors="coerce")
        pe = pd.to_numeric(fund.get("PE"), errors="coerce")
        fundamental_score = (
            (2 if pd.notna(market_cap) and market_cap >= 5_00_00_00_000 else 0)
            + (2 if pd.notna(revenue_growth) and revenue_growth > 0 else 0)
            + (2 if pd.notna(margin) and margin > 0 else 0)
            + (2 if pd.notna(debt_equity) and 0 <= debt_equity <= 2.5 else 0)
            + (2 if pd.notna(pe) and 0 < pe <= 60 else 0)
        )
        conviction = float(row["InvestorTechnicalScore"]) * 0.90 + fundamental_score

        confluence_score = int(pd.to_numeric(row.get("ConvergenceScore"), errors="coerce"))
        stage = row.get("Stage", 0)
        
        
        
        caution_stage = stage == 3
        suppressed_by_stage = stage == 4
        
        gated_confluence_score = confluence_score
        if not FILTERS_SHADOW_MODE:
            if caution_stage:
                gated_confluence_score = confluence_score * STAGE_3_PENALTY_MULTIPLIER
                conviction *= STAGE_3_PENALTY_MULTIPLIER
                
            if suppressed_by_stage:
                continue
            
        rows.append({
            "Symbol": row.get("Symbol"), "Company": row.get("Company"), "Setup": row.get("Setup"),
            "Investor Conviction": round(conviction, 1),
            "Technical Quality": round(float(row["InvestorTechnicalScore"]), 1),
            "Confluence": confluence_score,
            "Gated Confluence": round(gated_confluence_score, 1),
            "Stage": stage,
            "Caution Stage": caution_stage,
            "Suppressed By Stage": suppressed_by_stage,
            "Pattern": row.get("Pattern"),
            "Entry Quality": round(float(row.get("Entry_Quality", 0)), 1) if pd.notna(row.get("Entry_Quality")) else None,
            "RS Rating": round(float(row.get("RS_Rating", 0)), 1) if pd.notna(row.get("RS_Rating")) else None,

            "RS 3M %ile": round(float(row["RS3MPct"]), 1) if pd.notna(row.get("RS3MPct")) else None,
            "RS 6M %ile": round(float(row["RS6MPct"]), 1) if pd.notna(row.get("RS6MPct")) else None,
            "Volume x": round(float(row["VolumeRatio"]), 2) if pd.notna(row.get("VolumeRatio")) else None,
            "Liquidity": row.get("LiquidityBucket"),
            "RSI": round(float(row["RSI14"]), 2) if pd.notna(row.get("RSI14")) else None,
            "ATR %": round(float(row["ATRPercent"]), 2) if pd.notna(row.get("ATRPercent")) else None,
            "Gap %": round(float(row["GapPct"]), 2) if pd.notna(row.get("GapPct")) else None,
            "P/E": fund.get("PE"), "Revenue Growth %": fund.get("Revenue Growth %"),
            "Net Profit Margin %": fund.get("Profit Margin %"), "Debt/Equity": fund.get("Debt/Equity"),
            "EV/EBITDA": fund.get("EV/EBITDA"), "ROE %": fund.get("ROE %"), "Market Cap": fund.get("Market Cap"),
            "Yahoo Symbol": row.get("Yahoo Symbol"),
        })
    final = pd.DataFrame(rows)
    if final.empty:
        return final
    for col in ["Investor Conviction", "Technical Quality"]:
        final[col] = pd.to_numeric(final[col], errors="coerce")
    final = final.loc[final["Investor Conviction"] >= float(min_score)].sort_values(
        ["Investor Conviction", "Entry Quality", "Technical Quality", "RS 3M %ile"], ascending=False, na_position="last"
    ).reset_index(drop=True)
    if not final.empty:
        final.insert(0, "Rank", range(1, len(final) + 1))
    return final


def _build_emerging_scored(snapshot=None):
    """Shared Emerging scoring engine. No UI and no navigation dependency."""
    if snapshot is None:
        snapshot = get_snapshot()
    if not isinstance(snapshot, pd.DataFrame) or snapshot.empty or "DataQualityStatus" not in snapshot.columns:
        return pd.DataFrame()
    working = snapshot.loc[snapshot["DataQualityStatus"].astype(str).str.strip().eq("Insufficient history")].copy()
    if working.empty:
        return working

    def num(frame, col):
        return pd.to_numeric(frame[col], errors="coerce") if col in frame.columns else pd.Series(float("nan"), index=frame.index)
    score = pd.Series(0.0, index=working.index)
    for col, pts in [("BullMomentum",15),("BullSwing",15),("MomentumFresh",10),("VolumeConfirmedMomentum",10),("Breakout20",10)]:
        if col in working.columns:
            score += working[col].fillna(False).astype(bool).astype(float) * pts
    score += num(working,"RS3MPct").clip(0,100).fillna(0) * 0.15
    rsi = num(working,"RSI14")
    score += pd.Series(0.0,index=working.index).mask(rsi.between(50,70),5.0).mask(rsi.between(45,49.999999),3.0).mask(rsi.between(40,44.999999),1.0).mask(rsi.between(70.000001,75),3.0).fillna(0)
    working["Technical Score"] = score.clip(0,80).round(1)
    for col in ["Fundamental Score","Fundamental Coverage"]: working[col]=0.0
    working["Fundamental Coverage"] = 0
    for col in ["Revenue Growth %","Profit Margin %","Debt/Equity","P/E","EV/EBITDA", "ROE %","Market Cap"]: working[col]=float("nan")
    candidates = working.sort_values(["Technical Score","RS3MPct","VolumeRatio"],ascending=False,na_position="last").head(AI_FUNDAMENTAL_FETCH_LIMIT)
    for idx,row in candidates.iterrows():
        fund = _fundamental_for_scan("emerging_fundamentals_cache", row.get("Yahoo Symbol"))
        vals={
            "Revenue Growth %":pd.to_numeric(fund.get("Revenue Growth %"),errors="coerce"),
            "Profit Margin %":pd.to_numeric(fund.get("Profit Margin %"),errors="coerce"),
            "Debt/Equity":pd.to_numeric(fund.get("Debt/Equity"),errors="coerce"),
            "P/E":pd.to_numeric(fund.get("PE"),errors="coerce"),
            "EV/EBITDA":pd.to_numeric(fund.get("EV/EBITDA"),errors="coerce"),
            "ROE %":pd.to_numeric(fund.get("ROE %"),errors="coerce"),
            "Market Cap":pd.to_numeric(fund.get("Market Cap"),errors="coerce"),
        }
        rg,mg,de,pe,ev,roe=vals["Revenue Growth %"],vals["Profit Margin %"],vals["Debt/Equity"],vals["P/E"],vals["EV/EBITDA"],vals["ROE %"]
        fscore=(5 if pd.notna(rg) and rg>=15 else 3.5 if pd.notna(rg) and rg>0 else 1.5 if pd.notna(rg) and rg>-10 else 0)+(5 if pd.notna(mg) and mg>=15 else 3.5 if pd.notna(mg) and mg>0 else 1 if pd.notna(mg) and mg>-5 else 0)+(4 if pd.notna(de) and 0<=de<=1 else 3 if pd.notna(de) and de<=2 else 1.5 if pd.notna(de) and de<=3 else 0)+(3 if pd.notna(pe) and 0<pe<=30 else 2 if pd.notna(pe) and pe<=50 else 1 if pd.notna(pe) and pe<=75 else 0)+(3 if pd.notna(ev) and 0<ev<=20 else 2 if pd.notna(ev) and ev<=30 else 1 if pd.notna(ev) and ev<=50 else 0)
        for k,v in vals.items(): working.at[idx,k]=v
        working.at[idx,"Fundamental Score"]=round(min(fscore,20.0),1)
        working.at[idx,"Fundamental Coverage"]=sum(pd.notna(vals[k]) for k in ["Revenue Growth %","Profit Margin %","Debt/Equity","P/E","EV/EBITDA", "ROE %"])
    working["Emerging Score"]=(working["Technical Score"]+working["Fundamental Score"]).clip(0,100).round(1)
    def label(r):
        m=bool(r.get("BullMomentum",False)); sw=bool(r.get("BullSwing",False)); fr=bool(r.get("MomentumFresh",False)); br=bool(r.get("Breakout20",False)); vo=bool(r.get("VolumeConfirmedMomentum",False))
        if br and vo and m:return "Trend + Volume Breakout"
        if m and sw and fr:return "Fresh Momentum + Swing"
        if m and sw:return "Momentum + Swing"
        if br:return "Breakout Watch"
        if m:return "Momentum Watch"
        if sw:return "Swing Watch"
        return "Early Watch"
    working["Setup"]=working.apply(label,axis=1)
    return working


def build_emerging_buy_list(working):
    if not isinstance(working,pd.DataFrame) or working.empty:return pd.DataFrame()
    num=lambda c: pd.to_numeric(working[c],errors="coerce") if c in working.columns else pd.Series(float("nan"),index=working.index)
    buy=working.loc[num("Emerging Score")>=75].copy()
    buy=buy.loc[pd.to_numeric(buy["Technical Score"],errors="coerce")>=58].copy()
    buy=buy.loc[(pd.to_numeric(buy["RS3MPct"],errors="coerce") if "RS3MPct" in buy.columns else pd.Series(float("nan"),index=buy.index))>=70].copy()
    momentum=buy.get("BullMomentum",pd.Series(False,index=buy.index)).fillna(False).astype(bool)
    swing=buy.get("BullSwing",pd.Series(False,index=buy.index)).fillna(False).astype(bool)
    buy=buy.loc[momentum|swing].copy()
    buy=buy.loc[pd.to_numeric(buy["Fundamental Coverage"],errors="coerce")>=3].copy()
    buy=buy.loc[pd.to_numeric(buy["Fundamental Score"],errors="coerce")>=9].copy()
    traded=pd.to_numeric(buy["AvgTradedValue20"],errors="coerce") if "AvgTradedValue20" in buy.columns else pd.Series(0,index=buy.index)
    buy=buy.loc[traded.fillna(0)>=1_00_00_000].copy()
    return buy.sort_values(["Emerging Score","Fundamental Score","Technical Score","RS3MPct"],ascending=False,na_position="last").reset_index(drop=True)


