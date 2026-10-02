/**
 * @file DiseaseCare.tsx
 * @description Core component for DEM3T3R V1 architecture.
 * 
 * @project DEM3T3R V1
 * @author Pasindu Pathirana
 * @contact https://github.com/ppnpathirana/DEM3T3R-VI
 * @version 1.0.0
 * @date 2026
 * 
 * All rights reserved.
 */

import { useEffect, useRef, useState } from 'react';
import type { DiseaseItem } from '../App';

export default function DiseaseCare({ diseases, crop, request }: { diseases: DiseaseItem[]; crop: string; request: (name: string, confidence: number, crop: string, callback: (detail: any) => void) => (() => void) | undefined }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<(() => void) | undefined>();
  const [selected, setSelected] = useState<DiseaseItem | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => { cancel.current?.(); dialog.current?.close(); setSelected(null); return () => cancel.current?.(); }, [crop]);
  const open = (disease: DiseaseItem) => {
    cancel.current?.(); setSelected(disease); setDetail(null); setLoading(true);
    dialog.current?.showModal();
    cancel.current = request(disease.class, disease.confidence, crop, result => { setDetail(result); setLoading(false); });
  };
  const label = (name: string) => name.replace(/_/g, ' ');
  const lines = (value: unknown) => Array.isArray(value) ? value.filter(item => typeof item === 'string') : typeof value === 'string' ? [value] : [];
  return <section className="cg-card cg-care-card"><div className="cg-card-heading"><div><h2>Identified diseases & care plans</h2><p>{crop} · Select an observation to explore its care plan</p></div><span className="cg-pill">{diseases.length} observations</span></div>{diseases.length ? <div className="cg-care-list">{diseases.map((disease, index) => <button key={`${disease.class}-${index}`} onClick={() => open(disease)}><span><strong>{label(disease.class)}</strong><small>{Math.round(disease.confidence * 100)}% model confidence · {disease.count ?? 1} detections</small></span><span>View care plan →</span></button>)}</div> : <div className="cg-large-empty"><h3>Ready to take a closer look.</h3><p>Identified conditions appear here from the live camera analysis.</p></div>}
    <dialog ref={dialog} className="cg-dialog cg-care-dialog" onClose={() => cancel.current?.()}><div className="cg-dialog-heading"><span className="cg-pill">{crop} · Disease care</span><button className="cg-icon-button" aria-label="Close care plan" onClick={() => dialog.current?.close()}>✕</button></div><h2>{label(selected?.class ?? '')}</h2><p>Model confidence {Math.round((selected?.confidence ?? 0) * 100)}% · Confidence does not measure disease severity.</p>{loading ? <p role="status">Preparing your care plan…</p> : detail && <div className="cg-care-content"><p className="cg-care-notice">{detail.unavailable ? 'A disease-specific plan is unavailable. Try again when the advice service is connected.' : 'AI-generated guidance. Confirm the diagnosis and product label before treatment; dosage depends on formulation, crop, and local registration.'}</p>{detail.description && <section><h3>About this condition</h3><p>{detail.description}</p></section>}{detail.causes && <section><h3>Possible causes</h3><p>{detail.causes}</p></section>}<section><h3>Fertilizer & treatment plan</h3><p>Fertilizers support nutrition; disease-control products are separate treatments.</p>{Array.isArray(detail.fertilizer_list) && detail.fertilizer_list.length ? detail.fertilizer_list.map((item: any, i: number) => <article className="cg-treatment" key={i}><strong>{String(item.name ?? 'Suggested treatment')}</strong><dl><dt>Dosage</dt><dd>{String(item.dosage ?? 'Confirm product label and agronomist guidance')}</dd><dt>Application</dt><dd>{String(item.method ?? 'Not provided')}</dd></dl></article>) : <p>No verified product dosage is available for this observation.</p>}</section>{[['Recovery plan', detail.recovery_plan], ['Prevention', detail.prevention_tips]].map(([heading, value]) => <section key={String(heading)}><h3>{String(heading)}</h3>{lines(value).length ? <ol>{lines(value).map((line, i) => <li key={i}>{line}</li>)}</ol> : <p>Not available yet.</p>}</section>)}{detail.harvest_effect && <section><h3>Harvest outlook</h3><p>{detail.harvest_effect}</p></section>}{detail.spread_risk && <section><h3>Spread risk</h3><p>{detail.spread_risk}</p></section>}<button className="cg-button dark" onClick={() => selected && open(selected)}>Refresh care plan</button></div>}</dialog>
  </section>;
}
