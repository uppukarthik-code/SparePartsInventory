"""FINAL SYSTEM AUDIT (STEP20->28) — generate 15 audit CSVs (READ-ONLY; no analytics/output changes)."""
import os, sys, glob, hashlib
sys.path.insert(0,".")
import pandas as pd
from railway import railway_config as cfg
H = cfg.OUTPUT_DIR/"MAS"/"history"
def W(name, rows, cols):
    pd.DataFrame(rows, columns=cols).to_csv(H/name, index=False)

# SHA-256 guard over pre-existing outputs (exclude the 15 audit files we write)
AUDIT={ "repository_inventory.csv","data_foundation_audit.csv","forecast_audit.csv","lead_time_audit.csv",
 "criticality_audit.csv","safety_stock_audit.csv","rop_audit.csv","srrs_audit.csv","value_exposure_audit.csv",
 "operational_audit.csv","pipeline_consistency_audit.csv","software_engineering_audit.csv",
 "hardening_findings.csv","production_readiness_assessment.csv","final_architecture.csv"}
def tree():
    h={}
    for p in sorted(cfg.OUTPUT_DIR.rglob("*")):
        if p.is_file() and p.name not in AUDIT:
            h[str(p.relative_to(cfg.OUTPUT_DIR))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree()

# ---------- A: repository inventory (Source -> Consumer -> Output) ----------
W("repository_inventory.csv",[
 ("railway_demand_reconstruction.py","DMTR_*.xlsx (54)","STEP22/23","monthly_demand_history.csv +2","module"),
 ("railway_demand_classification.py","monthly_demand_history.csv","STEP23","demand_classification.csv,xyz,forecast_method_assignment","module"),
 ("railway_forecast_generation.py","monthly_demand_history,forecast_method_assignment","STEP24/25","forecast_results.csv,forecast_accuracy +2","module"),
 ("railway_lead_time_derivation.py","DMTR_*.xlsx","STEP24","lead_time_master.csv,pl_universe_reconciliation","module"),
 ("railway_pl_master.py","STEP22/23 csvs + sku_master + operational","audit","enterprise_pl_master,planning_master_data_audit +1","module"),
 ("railway_safety_stock.py","demand_classification,lead_time_master,SUMMARY,forecast_results","STEP25","safety_stock_results.csv,safety_stock_summary","module"),
 ("railway_rop.py","safety_stock_results,forecast_results,SUMMARY(027534)","STEP26","rop_results.csv,rop_summary","module"),
 ("railway_srrs_mas.py","rop_results,SUMMARY(Type,Rate),opt.service_factor","STEP27/28","srss_results.csv,srss_summary","module"),
 ("railway_inventory_optimization.py","(legacy) demand_history,sku_master,forecast","STEP24/25/26 reuse service_factor","railway_inventory_policy.csv","module(reused)"),
 ("railway_config.py","-","all modules","constants (some UNUSED by STEP20-28)","config"),
 ("_step*_run.py / _step*_audit.py (drivers)","modules","-","one-off; backward-compat guards","driver-scripts"),
 ("SUMMARY OF STOCK HELD*.xlsx","raw_data/.../MAS","STEP24/25/26/23.7/23.8/25.5","current stock, Type, Avg Rate","raw-source"),
 ("NS_DM_CONS_REPORT*.xlsx (7)","raw_data/.../MAS","STEP23.6A,27","procurement/lead-time corroboration","raw-source"),
 ("outputs/MAS/history/*.csv (41+)","modules+drivers","reports/dashboard","planning artifacts","outputs"),
],["Artifact","Source(Inputs)","Consumer(Downstream)","Output","Type"])

# ---------- B: data foundation ----------
W("data_foundation_audit.csv",[
 ("DMTR parsing (raw OOXML)","GREEN","54 files, 19618 txns, 0 null PL/date, 0 qty-fail (STEP21A QA)","robust enough; fragile to format change","keep; add schema assertions"),
 ("Issue aggregation (demand)","GREEN","Issues=Issue-To User Depot+For End Use+To Contractor; conserved 2,727,684","correct, traceable","none"),
 ("Double-counting risk","GREEN","one transaction->one type bucket; no overlap","not observed","none"),
 ("Under-counting risk","AMBER","Issue-Book Transfer & Write-Back excluded from demand","internal moves rightly excluded; but 'Issue-Other'-type would be missed","whitelist review"),
 ("Depot mixing","GREEN","demand=depot 027534 (DMTR); stock=027534 (SUMMARY)","consistent depot","none"),
 ("Closing_Stock reconstruction","AMBER","derived running balance; only 20/1083 reconcile vs stock_history(027029)","NOT a verified absolute; could mislead if used downstream","label clearly; do not use for planning"),
 ("Gap-fill missing months","GREEN","first-seen->2026-06 zero-fill; avoids leading-zero bias","standard for intermittent","none"),
 ("PL mismatch / universe","AMBER","DMTR(027534) vs operational(027029) overlap 20; criticality 32","near-disjoint ledgers; resolved for stock via SUMMARY 027534","unified PL master needed for rollout"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- C: forecast ----------
W("forecast_audit.csv",[
 ("SBC method assignment","GREEN","Erratic->Croston, Intermittent->SBA match Syntetos-Boylan 2005; Smooth->SES, Lumpy->TSB defensible","literature-aligned","note TSB-for-lumpy is post-SB2005 extension"),
 ("Cutoffs ADI 1.32 / CV2 0.49","GREEN","match Syntetos-Boylan 2005 verbatim","correct","none"),
 ("Engine reuse (Croston/SBA/TSB/Holt)","GREEN","imported verbatim from railway_forecasting; deterministic","no new algorithm","none"),
 ("12-month profile","AMBER","100% flat (annual=12x monthly); Seasonality_Modeled=No for all","no seasonality; honest given sparse intermittent data","disclose; revisit if monthly patterns emerge"),
 ("Accuracy metric (MAPE/sMAPE)","AMBER","Hyndman: sMAPE minimized by zero-forecast for intermittent; MAPE undefined on zeros","Forecastability acc=(1-sMAPE/200) unreliable for intermittent majority","add MASE as primary metric"),
 ("Backtest (rolling-origin)","GREEN","expanding window, 1-step, min24; 760/961 backtested","sound design","none"),
 ("Forecastability score","AMBER","fixed weights 0.35/0.25/0.15/0.15/0.10; accuracy term uses sMAPE","weights unvalidated; accuracy term weak","sensitivity test weights; MASE-based accuracy"),
 ("Method outperformance","AMBER","no cross-method bake-off per PL; assigned by class only","a different method could win per PL","optional per-PL backtest selection"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- D: lead time ----------
W("lead_time_audit.csv",[
 ("Chronology / negative intervals","GREEN","0 negative across 2821 obs (PO 1545, Reqn 1276)","clean","none"),
 ("PO vs Reqn semantics","AMBER","PO=vendor procurement(~131d median) vs Reqn=internal fulfilment(~81d); blended by hierarchy","two different lead-time definitions in one column","tag source (already in Lead_Time_Source); model separately if possible"),
 ("True replenishment LT?","AMBER","PO->Receipt is order-to-receipt (correct for procurement); Reqn->Receipt is internal","for Reqn-sourced PLs, LT may understate vendor replenishment","prefer PO; flag Reqn-only PLs"),
 ("Winsorization P5/P95","GREEN","global per-source; tames multi-year outliers (max capped 668/618d)","reasonable","none"),
 ("Empty-winsor edge","AMBER","np.median([]) would error if all intervals clipped out","latent crash (low likelihood)","add empty-guard"),
 ("Median aggregation","GREEN","median robust to skew; justified for lead-time","standard","none"),
 ("Coverage","AMBER","702/1083 PL (96% vol); 35% PL tail (4% vol) no LT","tail unplanned","accrue more receipts / PO master"),
 ("Confidence (n<5=Low)","AMBER","575 Low-confidence PLs (single-obs medians used)","wide uncertainty on tail","buffer conservatively"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- E: criticality (RED-TEAM) ----------
W("criticality_audit.csv",[
 ("'Safety Item' = safety-critical?","AMBER","stores 'PL-Code/Type/Usage' tag; validated recall 0.95 / precision 0.74 vs 32 S-coded items","proxy, NOT a consequence-based RAMS/VED assessment; 26% of Safety Items are S3/S4","engineer-led VED review for top items"),
 ("'Vital Item' = operational criticality?","AMBER","stores category; only 121 PLs; 1 validated overlap","weak independent validation for Vital","confirm with maintenance/ops"),
 ("Binary justified?","AMBER","collapses Safety/Vital/NA to Critical/Non-Critical","loses V/E/D granularity literature recommends","retain 3-way (Safety/Vital/NA) in SRRS already; expose as criticality tiers"),
 ("S1-S4 inference?","GREEN(by-omission)","NOT inferred; only binary asserted (evidence-gated, STEP23.8)","correctly avoided unsupported S-codes","extend master for true S1-S4"),
 ("False positives","AMBER","precision 0.74 -> ~26% over-classified Critical","conservative (over-protect) not under","acceptable for pilot"),
 ("False negatives","GREEN","recall 0.95 -> few true-critical missed","low miss rate","monitor"),
 ("Validation base size","RED-flag(weak-evidence)","only 32 common PLs (criticality master = 59 strategic)","conclusion rests on tiny sample","expand validated criticality set before full production"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- F: safety stock ----------
W("safety_stock_audit.csv",[
 ("Formula SS=z*sigma*sqrt(LT)","GREEN","recompute matches stored to <=0.005; z=norm.ppf(SL) correct","arithmetic correct","none"),
 ("Dimensional consistency","GREEN","sigma monthly * sqrt(LT_days/30.4375) = sqrt(months) -> qty","units consistent","none"),
 ("Normal approx for intermittent","RED(method)","z*sigma*sqrt(LT) assumes normal LT-demand; 86% items intermittent/lumpy; lit (Syntetos/Babai) flags inadequate","SS likely biased (over for lumpy/under for some); service level not actually guaranteed","use intermittent-demand SS (Croston-variance / bootstrap / distributional) for full production"),
 ("sigma derivation (monthly incl zeros)","AMBER","full-series std incl zero months; not size/interval decomposition","mis-estimates LT-demand variance for intermittent","compound/Poisson variance for intermittent classes"),
 ("Service level mapping","AMBER","Critical 0.95 / Non-Critical 0.85 hardcoded; cfg.SERVICE_LEVEL_TABLE unused","defensible defaults but not config-driven","centralise in config; sensitivity"),
 ("Binary criticality usage","AMBER","only 2 service tiers from binary criticality","coarse","tier by S1-S4 when available"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- G: ROP ----------
W("rop_audit.csv",[
 ("ROP=DDLT+SS","GREEN","recompute matches to <=0.005; no negative ROP","correct","none"),
 ("DDLT units","GREEN","Forecast_Annual*(LT_days/30.4375)/12 = annual*LT_days/365.25","unit-consistent","none"),
 ("Double counting","GREEN","forecast(mean) + SS(variability) are distinct terms","none observed","none"),
 ("Stock linkage","GREEN","Current_Stock from SUMMARY 027534 only; SS reused verbatim from STEP24","traceable","none"),
 ("Issuing-depot distortion","RED(operational)","465/626 Critical Shortage; depot 027534 holds ~0 of fast-movers","ROP-vs-stock overstates need for issuing depot; not a consignee buffer","net open POs; interpret as signal not absolute; confirm depot role"),
 ("Open-PO netting absent","AMBER","Net_Gap not computed; NS_DM_CONS covers 29/626","gaps not netted against pipeline","acquire full open-PO feed"),
 ("Stock-status thresholds","AMBER","0.5x/2x ROP hardcoded magic numbers","undocumented rationale","document/config"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- H: SRRS (sensitivity) ----------
W("srrs_audit.csv",[
 ("Formula reuse","GREEN","SRRS=CritWeight*ServiceFactor*Positive_Gap; service_factor imported verbatim","no formula change","none"),
 ("Effective weights","GREEN","backed out = {1,5,10} (NA/Vital/Safety) as intended","matches design","none"),
 ("Volume vs risk dominance","RED(interpretation)","Spearman(SRRS,Positive_Gap)=0.884; Top10 vs gap-rank overlap 8/10","SRRS is largely a (criticality-tilted) GAP/VOLUME ranking; 'service-risk' overstated","relabel as risk-weighted gap; report criticality contribution explicitly"),
 ("Sensitivity weight-ratio +/-20%","GREEN","Top10 stability=1.00, Top20=0.95","ranking robust to weight error","none"),
 ("Sensitivity service-factor +/-20%","GREEN","Top10=1.00 Top20=1.00 spearman=0.9995","robust","none"),
 ("Concentration","GREEN(evidence)","Top10=84.5% SRRS; compounded by issuing-depot gap inflation","focus valid but inflated by depot artifact","interpret with depot caveat"),
 ("Excess handling","AMBER","max(gap,0): excess stock contributes 0; cannot prioritise reduction","one-directional","separate excess/rationalisation lens (exists in legacy)"),
 ("Rank ties","AMBER","method='first' (input-order tiebreak)","reproducible given stable input; not value-based","tie-break by criticality then value"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- I: value exposure ----------
W("value_exposure_audit.csv",[
 ("Gap Value=Gap*Unit Rate","GREEN","Average Rate 100% coverage, internally consistent (Value=Stock*Rate 99.3%)","correct","none"),
 ("Unit-cost validity","GREEN","SUMMARY col11; 820 distinct; range Rs0.95-6.83M","real source","none"),
 ("Adds decision quality vs SRRS?","GREEN","Spearman(SRRS,Value)=0.746; Top20 overlap only 6 -> distinct dimension","not duplicative; complementary","keep as separate axis"),
 ("Concentration / outliers","AMBER","Top10=74.1% value; few extreme unit-cost items (Rs6.83M) dominate","ranking skewed by outliers","present with SRRS, not alone; winsorise display"),
 ("Exposure != savings","GREEN(framing)","reported as exposure Rs3.37B, not savings","no fabricated savings","maintain framing"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- J: operational ----------
W("operational_audit.csv",[
 ("SRRS operational validity","AMBER","Top-50 all High/Med importance; but volume-dominated (see SRRS audit)","priorities sensible but volume-led","pair with criticality + open-PO"),
 ("Deployment readiness","AMBER","pilot-ready (human-in-loop); not unsupervised automation","method-correct, data caveats","supervised pilot only"),
 ("Dashboard","AMBER","designed (7 views), not built","no live tool yet","build on BI tool"),
 ("Rollout assumptions","RED(data)","5 divisions have only stock_history; no DMTR/SUMMARY -> STEP21A blocked","enterprise rollout blocked on data acquisition","acquire per-division DMTR+SUMMARY"),
 ("Org feasibility","AMBER","owners 'illustrative'; depends on stores org adoption","change-management risk","confirm roles, train, pilot"),
 ("PO netting","AMBER","feasible but covers 29/626 (1 open-PO overlap)","cannot net most priorities yet","full open-PO feed"),
 ("Missing data","AMBER","lead-time tail, S1-S4 criticality, full PO feed, depot role confirmation","known gaps","roadmap"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- K: pipeline consistency ----------
W("pipeline_consistency_audit.csv",[
 ("Funnel PL counts","GREEN","demand 1083 -> forecast 961 -> LT 702 -> SS 626 -> ROP 626 -> SRRS 626","monotone, explained (Dead/LT-tail)","none"),
 ("Unique PLs each stage","GREEN","all stages PL-unique","no duplicates","none"),
 ("Subset integrity","GREEN","SS subset of forecast; ROP==SS set; SRRS==ROP set","dependency-consistent","none"),
 ("SS reused verbatim into ROP","GREEN","max|SS diff|=0 between STEP24 and STEP25 input","no recompute drift","none"),
 ("Volume conservation (demand)","GREEN","Issues 2,727,684 conserved (STEP21A); forecast annual=12*monthly","conserved","none"),
 ("Coverage consistency","GREEN","626 PLs = 96% forecast volume at SS/ROP/SRRS","consistent across layers","none"),
 ("Backward compatibility","GREEN","every STEP20-28 step SHA-256: 0 prior outputs changed","strict additivity verified","none"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- L: software engineering ----------
W("software_engineering_audit.csv",[
 ("Modularity","GREEN","one module per step; clear single responsibility","good","none"),
 ("Reuse / no-duplication","GREEN","service_factor, forecasting fns, raw-XML reader reused","DRY","none"),
 ("Configuration handling","AMBER","DAYS_PER_MONTH, service levels, weights hardcoded in modules; cfg tables unused","drift/maintainability","centralise constants in config"),
 ("Validation coverage","AMBER","per-step driver checks + SHA-256; NO unit/integration test suite","regressions undetected","add pytest suite"),
 ("Reproducibility","GREEN","deterministic (fixed alpha/seedless); byte-identical re-runs","strong","none"),
 ("Traceability","GREEN","every output traces to source; drivers retained","auditable","none"),
 ("Error handling","AMBER","fragile regex; bare excepts->0.0; empty-median edge; silent depot drop","silent data loss / latent crash","explicit validation + logging"),
 ("Orchestration","AMBER","one-off _step*_run.py drivers, not a pipeline/DAG","manual, order-dependent","wrap in a runner/Makefile/DAG"),
 ("Coupling","GREEN","CSV-contract coupling between steps (loose)","acceptable","schema-validate CSVs"),
 ("Cybersecurity","GREEN","offline batch, no network/PII/secrets/endpoints","minimal attack surface","sanitise if exposed via dashboard"),
],["Check","Status","Evidence","Risk","Recommendation"])

# ---------- M: hardening findings (RED/AMBER/GREEN) ----------
W("hardening_findings.csv",[
 ("F01","RED","SS normal-approximation (z*sigma*sqrt(LT)) on 86% intermittent/lumpy demand","railway_safety_stock.py + Syntetos/Babai lit","SS bias; stated service level not guaranteed","High","Use intermittent-demand SS (bootstrap/Croston-variance/distributional) before unsupervised automation"),
 ("F02","RED","SRRS is gap/volume-dominated (Spearman 0.884; 8/10 top match gap), compounded by issuing-depot inflation","srrs_audit recompute","'service-risk' label overstates criticality role; misallocation risk","Medium","Relabel as risk-weighted gap; net open POs; report criticality contribution"),
 ("F03","RED","Issuing-depot ROP distortion: 465/626 Critical Shortage at depot 027534 (holds ~0 fast-movers)","rop_results status dist","over-procurement signal if taken literally","High","Net open POs; confirm depot role; treat as relative signal"),
 ("F04","RED","Forecast accuracy/forecastability uses sMAPE/MAPE (inappropriate for intermittent; sMAPE->zero-forecast optimum)","forecast_accuracy + Hyndman lit","unreliable accuracy/forecastability for intermittent majority","Medium","Adopt MASE as primary metric; recompute forecastability accuracy term"),
 ("F05","RED","Enterprise rollout blocked: 5/6 divisions lack DMTR/SUMMARY","division folders","system validated on 1 division only","High","Acquire per-division DMTR+SUMMARY before zone claims"),
 ("F06","AMBER","Criticality is binary stores-proxy validated on 32 PLs (precision 0.74), not RAMS/VED","criticality_signal_validation","mis-tiering; weak validation base","Medium","Engineer-led VED for top items; expand validated set"),
 ("F07","AMBER","Lead-time mixes PO(vendor) & Reqn(internal) semantics via hierarchy+median","lead_time_master Lead_Time_Source","SS/ROP LT inconsistent across PLs","Medium","Prefer PO; flag/segregate Reqn-only"),
 ("F08","AMBER","Config drift: constants hardcoded in modules; cfg.SERVICE_LEVEL_TABLE/STOCKOUT_WEIGHT unused","railway_config vs modules","maintainability; silent divergence","Medium","Centralise in config; remove dead config"),
 ("F09","AMBER","No automated test suite; orchestration via one-off drivers","repo","regressions/reproducibility risk at scale","Medium","pytest + pipeline runner"),
 ("F10","AMBER","Fragile regex parsing + silent except->0.0 + empty-median edge + silent non-027534 drop","modules","silent data loss / latent crash","Low-Med","explicit schema validation + guards + logging"),
 ("F11","AMBER","Closing_Stock reconstructed, weakly reconciled (20-PL overlap)","data_foundation_audit","misuse risk if treated as actual","Low","label derived; exclude from planning"),
 ("F12","AMBER","Lead-time/SS/ROP/SRRS tail: 35% PL (4% vol) uncovered","funnel","tail items unplanned","Low","accrue receipts / PO master"),
 ("F13","AMBER","SRRS excess (max(gap,0)) cannot prioritise overstock reduction","srrs_mas.py","one-directional optimisation","Low","separate excess lens"),
 ("F14","GREEN","Formulas (SS,ROP,SRRS) dimensionally correct & recompute to <=0.005","verification driver","-","-","Maintain"),
 ("F15","GREEN","Strict backward compatibility (0 prior outputs changed, all steps)","SHA-256 per step","-","-","Maintain"),
 ("F16","GREEN","SBC cutoffs & method assignment match Syntetos-Boylan 2005","forecast_audit + lit","-","-","Maintain"),
 ("F17","GREEN","No synthetic demand/LT/criticality/stock/savings; honest coverage flagging","all steps","-","-","Maintain"),
 ("F18","GREEN","Pipeline funnel consistent & dependency-integral; reproducible","pipeline_consistency_audit","-","-","Maintain"),
],["ID","RAG","Finding","Evidence","Impact","Likelihood","Recommendation"])

# ---------- N: production readiness ----------
W("production_readiness_assessment.csv",[
 ("Data Foundation",78,"High","demand reconstruction conserved, 0 nulls; closing-stock weak; near-disjoint universes resolved via SUMMARY","closing-stock, universe rollout"),
 ("Forecasting",65,"Medium","SBC-aligned, reproducible; flat profile; sMAPE metric inappropriate for intermittent","metric (MASE), flat profile"),
 ("Lead Time",70,"Medium","chronology-clean, 96% vol; mixed PO/Reqn semantics; 35% PL tail","semantics, tail"),
 ("Criticality",58,"Low-Med","99.6% binary coverage, recall 0.95; stores-proxy not RAMS; 32-PL validation","weak validation base, binary"),
 ("Safety Stock",55,"Low-Med","arithmetic correct; normal-approx inappropriate for intermittent majority","method for intermittent"),
 ("ROP",62,"Medium","mechanics correct; issuing-depot distortion; no PO netting","depot artifact, netting"),
 ("SRRS",60,"Medium","reused objective, stable, reproducible; volume-dominated; excess unhandled","volume dominance, labeling"),
 ("Value Exposure",72,"Medium-High","100% unit-rate, complementary to SRRS; outlier-skewed","outliers"),
 ("Operationalization",55,"Low-Med","portfolio sound, dashboard designed not built; pilot-ready","build, adoption"),
 ("Governance",50,"Low-Med","config drift, no tests, illustrative owners, provenance caveats","tests, config, ownership"),
 ("Software Engineering",55,"Low-Med","modular/reproducible/backward-compatible; no tests, hardcoded, fragile parsing","tests, robustness, orchestration"),
],["Dimension","Score_0_100","Confidence","Evidence","Key_Risks"])

# ---------- O: final architecture ----------
W("final_architecture.csv",[
 ("RAW","DMTR_*.xlsx (monthly transactions)","MANDATORY","demand history source"),
 ("RAW","SUMMARY OF STOCK HELD (depot stock+Type+Rate)","MANDATORY","current stock, criticality proxy, unit cost"),
 ("RAW","NS_DM_CONS (procurement/PO)","OPTIONAL","lead-time corroboration, future PO netting"),
 ("RAW","engineer-led VED/criticality master","FUTURE-MANDATORY","replace stores-proxy criticality"),
 ("PROCESSING","demand reconstruction -> classification (SBC)","MANDATORY","monthly demand + demand class"),
 ("PROCESSING","lead-time derivation (PO/Reqn->Receipt)","MANDATORY","Lead_Time_Days"),
 ("PROCESSING","PL master reconciliation","MANDATORY","canonical PL key"),
 ("PLANNING","forecast (Croston/SBA/TSB/SES) + MASE metric","MANDATORY (add MASE)","per-PL forecast"),
 ("PLANNING","safety stock (intermittent-aware for full prod)","MANDATORY (upgrade method)","SS"),
 ("PLANNING","ROP + reorder gap (net open POs)","MANDATORY (add netting)","ROP, Net_Gap"),
 ("PRIORITIZATION","SRRS (risk-weighted gap) + value lens","MANDATORY","priority + exposure"),
 ("PROCUREMENT","tiered portfolio + dashboard","MANDATORY (build dashboard)","action worklist"),
 ("ENHANCEMENT","S1-S4 criticality, seasonality, bootstrap SS, enterprise rollout, test suite","FUTURE","hardening"),
],["Layer","Component","Necessity","Role"])

after=tree()
changed=[k for k in before if before[k]!=after.get(k)]
print("Audit CSVs written:",len([f for f in AUDIT if (H/f).exists()]),"/15")
print("Backward-compat: existing files changed =",len(changed),"UNCHANGED:",not changed)
