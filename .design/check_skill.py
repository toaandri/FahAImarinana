from pathlib import Path
import re,zipfile
s=Path('.github/skills/fahaimarinana-react/SKILL.md');t=s.read_text(encoding='utf-8');assert t.startswith('---\nname: fahaimarinana-react\ndescription: ');assert '\n---\n' in t
for m in s.parent.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',m.read_text(encoding='utf-8')):
  if not '://' in link:assert (m.parent/link).exists(),link
with zipfile.ZipFile('FahAIMarinana-Skill-Copilot-React.zip') as z:assert z.testzip() is None
print('Structure, liens locaux et archive vérifiés. Validateur officiel indisponible : dépendance PyYAML absente.')
