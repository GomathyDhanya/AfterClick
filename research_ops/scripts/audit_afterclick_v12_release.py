import json,hashlib,csv,collections,shutil
from pathlib import Path
root=Path('/Users/gomathydhanya/projects/684_final');pkg=root/'research_ops/completion_v12/final_package';idx=json.loads((pkg/'RELEASE_INDEX.json').read_text());out=root/idx['evidence_root']
def load(p):return json.loads(p.read_text())
f=load(root/idx['freeze']);checked={}
for category in ['source_hashes','gate_hashes']:
 for name,sha in f[category].items():
  p=Path(name);p=p if p.is_absolute() else root/p
  actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==sha,name;checked[name]=actual
matrix=list(csv.DictReader((pkg/'FROZEN_MATRIX_RECONCILIATION.csv').open()));assert len(matrix)==2904
assert len({(r['model'],r['episode_id']) for r in matrix})==2904
c=collections.Counter(r['status'] for r in matrix)
models={}
for tag in ['primary','larger']:
 verification=load(root/idx[tag]['verification']);assert verification['passed'] and verification['disagreements']==0
 extended=load(out/f'{tag}-extended-graph-verification/report.json');assert extended['passed']
 table=load(root/Path(idx[tag]['analysis_report']).parent/'episode-table.json')
 models[tag]=dict(registered=len(table),terminal=sum(x['status']!='NOT_RUN' for x in table),valid=sum(x['status']=='VALID' for x in table),task_contracts_with_terminal_records=len({x['task_id'] for x in table if x['status']!='NOT_RUN'}),independent_oracle=verification,extended_graph=extended)
report=dict(artifact_checks_passed=True,research_acceptance_passed=False,full_matrix_complete=False,registered=2904,terminal=1479,unexecuted=1425,statuses=dict(c),frozen_files_unchanged=len(checked),models=models,nonfinancial_requirement_gaps=['No separately executed cached-equivalent or irrelevant-verification arms','No separately executed no-restoration-needed or adversarial-restoration arms','No reconstructed exact mid-trajectory counterfactual branches','No exact worker authorization-read or SQL-COMMIT boundary','P5 queue-hold is a suspension-first proxy, not semantic staging','Independent software oracle implementation is not independent human review'],financial=load(pkg/'FINAL_FINANCIAL_SUMMARY.json'),no_false_completion_claim=True)
(pkg/'FINAL_ACCEPTANCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile('/tmp/afterclick-final-tests.log',out/'final-targeted-tests.log')
(pkg/'CLAIM_TO_EVIDENCE.md').write_text('''# Final claim-to-evidence audit

The research acceptance decision is **FAIL / INCOMPLETE**. Software and artifact validation does not convert unexecuted trials into results.

| Claim | Evidence | Scope and limitation |
|---|---|---|
| 72 DEV and 216 TEST contracts implemented | TASK_CATALOG.csv; candidate_contracts_v7 | Compositional six-family, two-app benchmark |
| 576 executable safe reference witnesses | v12-20 qualification; v12-40 independent verifier | Separate software implementations; no human audit |
| 10,944 evidence/obligation mutations rejected | v12-40 independent verifier | Mutation coverage does not prove arbitrary oracle correctness |
| 1,479 of 2,904 frozen TEST assignments recorded | FROZEN_MATRIX_RECONCILIATION.csv | 1,425 never started; invalid records retained |
| 905 primary records on 185 distinct TEST contracts | Final primary episode table | 216 designed contracts are not 216 fully evaluated contracts |
| 334 larger records on all 36 preselected contracts | Final larger episode table | 26 unexecuted conditions; model scale is confounded |
| All 240 official external conditions executed | Final official-external-analysis | 12 official tasks, two context seeds, five wrappers; EvoUndo unavailable |
| No checker disagreements on recorded internal outcomes | Final independent oracle reports | 1,239 terminal records, 1,073 valid; invalidity checked separately |
| Real time-indexed trajectories and initial safe alternatives | Final graphs, raw-reference and extension verifiers | Intermediate recoverability UNKNOWN; no arbitrary cut reconstruction |
| Controlled actual enforcement delays increase forbidden history | v12-31 branches; v12-37 analysis | 12 constructed sources; one invalid; total actuator effect, not pure LLM latency |
| $18 cap respected by conservative guards | FINANCE_STATE; FINAL_FINANCIAL_SUMMARY; fresh closure proofs | $17.96725281; no isolated invoice; $0 billed in fresh account snapshot |

No general controller superiority, novel staging mechanism, live formal recoverability certificate, full second-model replication, or complete research program is claimed. UNMET_REQUIREMENTS.md records the specification gaps.
''')
print(json.dumps(dict(statuses=dict(c),files=len(checked),models={k:{a:v[a] for a in ['registered','terminal','valid','task_contracts_with_terminal_records']} for k,v in models.items()})))
