from pathlib import Path
import json, re

root=Path(__file__).resolve().parents[1]
registry=json.loads((root/'sources.json').read_text(encoding='utf-8'))
local={x['name'] for x in registry['skills'] if x['repo']=='zjc20030326/personal-agent-skills'}
found={p.name for p in (root/'skills').iterdir() if p.is_dir()}
assert found==local,(found,local)
for name in sorted(found):
    p=root/'skills'/name/'SKILL.md'
    s=p.read_text(encoding='utf-8-sig')
    assert s.startswith('---'),p
    header=s.split('---',2)[1]
    match=re.search(r'^name:\s*["\']?([^\r\n"\']+)',header,re.M)
    assert match and match.group(1).strip()==name,p
    assert re.search(r'^description:',header,re.M),p
for p in root.rglob('*'):
    if '.git' in p.parts:continue
    assert p.name not in ('.env','.credentials.yaml','cc-switch.db'),p
print(f'Validated {len(found)} repository packages and {len(registry["skills"])} source records.')
