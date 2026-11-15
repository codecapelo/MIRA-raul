"""Medicare-based national price proxy per CPT/HCPCS code. Local tables only (CPT codes and short descriptions are AMA copyright; data/cpt/ is Git-ignored).

Sources (CMS, public files):
  * RVU26D  PPRRVU2026_*.csv  Physician Fee Schedule relative values. Price = total RVU x conversion factor (column CONV FACTOR, read from the file itself).
    Imaging and procedures. Laboratory codes appear there with status X (not paid under the PFS) and zero RVUs: they are NOT priced from this file.
  * CLFS  26CLABQ4*.csv  Clinical Laboratory Fee Schedule (national limit amounts). Needs the user to accept the AMA licence and download it; optional here.

Basis: national, non-facility (the whole service, as if ordered in an office/outpatient setting) unless `setting='facility'`. A code with professional (26) and technical (TC) components is priced as the global service
(row with no modifier); `component='26'` or `'TC'` selects one part. This is a transparent proxy for relative cost, not the cost to any hospital or the charge to any patient.
"""
import csv
from pathlib import Path

class PriceUnavailable(KeyError):pass

def _rows(path):
    with open(path,newline='',encoding='latin-1') as f:return list(csv.reader(f))

def load_pfs(path):
    """-> {(code,modifier): {'nonfacility_rvu','facility_rvu','status','conversion_factor','description'}}"""
    rows=_rows(path);head=next(i for i,r in enumerate(rows) if r and r[0].strip()=='HCPCS')
    out={}
    for r in rows[head+1:]:
        if len(r)<26 or not r[0].strip():continue
        try:out[(r[0].strip().upper(),r[1].strip().upper())]={'status':r[3].strip(),'nonfacility_rvu':float(r[11] or 0),'facility_rvu':float(r[12] or 0),'conversion_factor':float(r[25] or 0),'description':r[2].strip()}
        except ValueError:continue
    return out

def load_clfs(path):
    """CLFS CSV: finds the header row with HCPCS and RATE columns. -> {code: rate_usd}"""
    rows=_rows(path);out={}
    for i,r in enumerate(rows):
        names=[c.strip().upper() for c in r]
        if 'HCPCS' in names and any(n in ('RATE','NATIONAL LIMIT AMOUNT') for n in names):
            ci=names.index('HCPCS');ri=names.index('RATE') if 'RATE' in names else names.index('NATIONAL LIMIT AMOUNT')
            for q in rows[i+1:]:
                if len(q)>max(ci,ri) and q[ci].strip():
                    try:out[q[ci].strip().upper()]=float(q[ri].replace('$','').replace(',','') or 0)
                    except ValueError:continue
            break
    return out

class PriceTable:
    def __init__(self,pfs,clfs=None,setting='nonfacility'):
        if setting not in ('nonfacility','facility'):raise ValueError('setting must be nonfacility or facility')
        self.pfs,self.clfs,self.setting=pfs,clfs or {},setting
    @classmethod
    def from_dir(cls,directory,setting='nonfacility'):
        d=Path(directory);pfs=load_pfs(d/'rvu26d/PPRRVU2026_Oct_nonQPP.csv') if (d/'rvu26d').exists() else load_pfs(next(d.glob('PPRRVU*nonQPP.csv')))
        lab=next(iter(sorted(d.glob('**/CLAB*.csv'))+sorted(d.glob('**/26CLAB*.csv'))),None)
        return cls(pfs,load_clfs(lab) if lab else {},setting)
    def price(self,code,component=None):
        """USD for one unit. component: None (global), '26' or 'TC'. Raises PriceUnavailable when the code has no payable price in the loaded tables."""
        code=str(code).strip().upper();mod=(component or '').upper()
        if mod not in ('','26','TC'):raise ValueError('component must be None, 26 or TC')
        row=self.pfs.get((code,mod))
        if row and row['status'] in 'ACRT' and row['status']:
            rvu=row['nonfacility_rvu'] if self.setting=='nonfacility' else row['facility_rvu']
            if rvu>0 and row['conversion_factor']>0:return round(rvu*row['conversion_factor'],2)
        if not mod and code in self.clfs and self.clfs[code]>0:return round(self.clfs[code],2)
        raise PriceUnavailable(code)
    def describe(self,code):
        r=self.pfs.get((str(code).strip().upper(),''));return r['description'] if r else None

def order_cost(table,mapping,exam_name,*,default_unit=1):
    """mapping: {normalised exam name: {'cpt':[codes],'units':n}}. Returns {'usd':float|None,'codes':[...],'unpriced':[...]}; never invents a price for an unmapped or unpriced code."""
    entry=mapping.get(exam_name.strip().lower())
    if not entry:return {'usd':None,'codes':[],'unpriced':[exam_name]}
    total=0.0;priced=[];unpriced=[]
    for code in entry['cpt']:
        try:total+=table.price(code)*entry.get('units',default_unit);priced.append(code)
        except PriceUnavailable:unpriced.append(code)
    return {'usd':round(total,2) if priced else None,'codes':priced,'unpriced':unpriced}
