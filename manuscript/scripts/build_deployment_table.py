"""Resume receipts de implantação retidos; não executa EVM nem modifica dados."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'results/final-gas-20261026-attempt05'
load = lambda p: json.loads(p.read_text())
inventory = load(DATA/'artifact-hashes.json')
files=[]
def checked(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==inventory[str(path.relative_to(DATA))]
    files.append(path)
    return load(path)
broadcast=checked(DATA/'project/broadcast/DeployFinal.s.sol/11155111/run-latest.json')
links=checked(DATA/'linked-libraries.json')
addresses=checked(DATA/'addresses.json')
receipts={r['transactionHash']:r for r in broadcast['receipts']}
deploy={}
for tx in broadcast['transactions']:
    path=DATA/f"deploy-{tx['contractAddress']}.json";d=checked(path)
    assert d['broadcast']==tx and d['receipt']==receipts[tx['hash']]
    assert int(d['receipt']['status'],16)==1
    assert hashlib.sha256(bytes.fromhex(d['code'][2:])).hexdigest()==d['runtime_sha256']
    deploy[tx['contractAddress'].lower()]=d
assert len(deploy)==16 and len(links)==8 and len(addresses)==8
names=['Field diagnóstico','u8','u32','u64','Field restrito 8','Field restrito 32','Field restrito 64','u64 com compromisso']
fmt=lambda n:f'{n:,}'.replace(',',r'\,')
rows=[]; seen=set()
for name,link in zip(names,links):
    verifier=deploy[addresses[link['verifier']].lower()];library=deploy[link['address'].lower()]
    assert verifier['broadcast']['transactionType']=='CREATE'
    assert library['broadcast']['transactionType']=='CREATE2'
    assert library['broadcast']['contractName']==link['library']
    for d in (verifier,library):
        h=d['receipt']['transactionHash'];assert h not in seen;seen.add(h)
    vg=int(verifier['receipt']['gasUsed'],16);lg=int(library['receipt']['gasUsed'],16)
    rows.append({'name':name,'verifier':link['verifier'],'verifier_gas':vg,'library_gas':lg,'sum_gas':vg+lg,
                 'verifier_tx':verifier['receipt']['transactionHash'],'library_tx':library['receipt']['transactionHash']})
assert len(seen)==16 and sum(r['sum_gas'] for r in rows)==sum(int(d['receipt']['gasUsed'],16) for d in deploy.values())
content=[r'\begin{table}[htbp]',r'\centering',r'\caption{Gas total de implantação dos verificadores e bibliotecas vinculadas}',r'\label{tab:implantacao}',r'\begin{tabular}{lrrr}',r'\hline',r'Variante & Verificador & Biblioteca & Soma \\',r'\hline']
content += [r['name']+' & '+' & '.join(fmt(r[k]) for k in ('verifier_gas','library_gas','sum_gas'))+r' \\' for r in rows]
content += [r'\hline',r'\end{tabular}',r'\par\smallskip',r'\begin{minipage}{\textwidth}',r'\renewcommand{\baselinestretch}{1}\small',r'Fonte: elaboração própria a partir dos recibos da rodada de 26/10/2026.\par',r'Nota: valores em unidades de gas; uma transação por verificador (CREATE) e por biblioteca (CREATE2). Soma dos dois recibos associados à variante, sem amortização ou custo de infraestrutura previamente disponível no fork. Mesma configuração da Tabela~\ref{tab:gas}.',r'\end{minipage}',r'\end{table}']
out=ROOT/'manuscript/tables/deployment-costs.tex';out.write_text('\n'.join(content)+'\n')
files += [Path(__file__),out]
report={'rows':rows,'receipts_checked':16,'total_gas':sum(r['sum_gas'] for r in rows),'hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(ROOT/'manuscript/validation/deployment-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print('16 receipts conferidos; total:',report['total_gas'])
