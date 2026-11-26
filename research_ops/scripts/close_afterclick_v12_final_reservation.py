import json,hashlib,fcntl
from pathlib import Path
root=Path(__file__).resolve().parents[2];run=root/'artifacts/research_runs/v12-68-final-credit-bound-continuation';statepath=root/'research_ops/completion_v12/FINANCE_STATE.json'
def load(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
actual=dict(calls=0,tokens=0,uncertain=0)
for p in sorted(run.glob('cloud-batches/*/*/runtime.json')):
 for k,v in load(p)['usage'].items():actual[k]+=v
for k,v in load(run/'external-usage.json').items():actual[k]+=v
assert actual['calls']==6405 and actual['uncertain']==0,actual
save(run/'recovered-usage-reconciliation.json',dict(original_lifecycle_usage=load(run/'lifecycle.json')['usage'],recovered_all_batch_usage=actual,actual_unknown_responses=0,original_lifecycle_has_one_batch_accounting_sentinel=True,all_original_records_unchanged=True,scope='Five complete verified batch archives plus external usage; no generation retried'))
with (root/'research_ops/SPEND_STATE.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 s=load(statepath);assert s['active'] is None and s['runs'][-1]['run_id']==run.name
 raw=run/'raw';assert load(raw/'containers-after-cpu-stop.json')==[]
 assert load(raw/'cpu-app-stopped-proof.json')['lifecycle']['state']=='stopped'
 billing=load(raw/'billing-closeout-proof.json');assert float(billing['billed_cost'])==0
 settings=load(raw/'settings-final-min0.json')['current_settings'];assert settings['min_containers']==0 and settings['buffer_containers']==0
 folder=raw/'retained-reservation-closeout';folder.mkdir(exist_ok=False)
 (folder/'ledger-before.json').write_bytes(statepath.read_bytes())
 names=['containers-after-cpu-stop.json','cpu-app-stopped-proof.json','billing-closeout-proof.json','settings-final-min0.json']
 proof=dict(financial_lifecycle_closed=True,original_lifecycle_idle_check_failed=True,current_producers_stopped=True,current_endpoint_containers_empty=True,full_reservation_retained_usd=1.55,adjustment_usd=0,actual_unknown_responses=0,original_accounting_uncertainty_sentinel_preserved=True,no_new_model_calls=True,actual_isolated_invoice_usd=None,evidence={str((raw/n).relative_to(root)):hashlib.sha256((raw/n).read_bytes()).hexdigest() for n in names})
 save(folder/'proof.json',proof)
 s['runs'].append(dict(run_id=run.name+'-retained-reservation-closeout',parent=run.name,reserved_usd=0,guard_charge_usd=0,usage=dict(calls=0,tokens=0,uncertain=0),idle_verified=True,original_guard_charge_unchanged=1.55,scientific_unknown_responses_preserved=0,accounting_sentinel_preserved_in_original_lifecycle=True,evidence=str((folder/'proof.json').relative_to(root)),actual_isolated_invoice_usd=None,note='Fresh stopped-producer and empty-GPU proofs close future request exposure. Full prior reservation retained; no original lifecycle or usage rewritten.'))
 s['unresolved_request']=False
 temp=statepath.with_suffix('.closeout.tmp');save(temp,s);temp.replace(statepath)
 print(json.dumps(dict(actual_usage=actual,guard=sum(r['guard_charge_usd'] for r in s['runs']),proof=proof)))
