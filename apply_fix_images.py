import re
from pathlib import Path
root=Path(r"c:/Users/abdul/Desktop/Neat MicroCredit .com")
imgs={p.name for p in (root/'images').glob('*') if p.is_file()}
htmls=sorted((root/'html').glob('*.html'))
pattern_src=re.compile(r"(?i)(src|href)\s*=\s*([\"'])(?![A-Za-z][A-Za-z0-9+.-]*:|/|\.\.?/|images/)([^\"']+\.(?:png|jpe?g|gif|svg|webp|bmp))\2")
pattern_url=re.compile(r"(?i)url\(\s*([\"']?)(?![A-Za-z][A-Za-z0-9+.-]*:|/|\.\.?/|images/)([^\"')]+\.(?:png|jpe?g|gif|svg|webp|bmp))\1\s*\)")
patched=[]
for f in htmls:
    t=f.read_text(encoding='utf-8',errors='replace')
    orig=t
    def rep_src(m):
        path=m.group(3)
        name=Path(path).name
        if name in imgs:
            return f"{m.group(1)}={m.group(2)}../images/{name}{m.group(2)}"
        return m.group(0)
    t=pattern_src.sub(rep_src,t)
    def rep_url(m):
        path=m.group(2)
        name=Path(path).name
        if name in imgs:
            q=m.group(1) or ''
            return f"url({q}../images/{name}{q})"
        return m.group(0)
    t=pattern_url.sub(rep_url,t)
    if t!=orig:
        f.write_text(t,encoding='utf-8')
        patched.append(f.name)
print('patched_files:', patched)
# list remaining bare references
remaining=[]
for f in htmls:
    txt=f.read_text(encoding='utf-8',errors='replace')
    if re.search(r"(?i)(?:src|href)\s*=\s*[\"'](?!\.\.?/|images/|https?://|data:)([^\"']+\.(?:png|jpe?g|gif|svg|webp|bmp))[\"']", txt):
        remaining.append(f.name)
print('files_with_bare_refs:', remaining)
