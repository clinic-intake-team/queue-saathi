export type Row = Record<string, string>
export type Datasets = Record<string, Row[]>
export type Metrics = { medicineOff: number; medicineOn: number; caught: string; falseAlarms: string; version: string }

// Source selection is explicit: never combine official v1 with development v2.
export function landingMetrics(datasets: Datasets): Metrics {
  const a = datasets.setA_summary
  const off = a?.find(r => r.speaker === 'overall' && r.condition === 'keyterms_off')
  const on = a?.find(r => r.speaker === 'overall' && r.condition === 'keyterms_on')
  const bName = ['setB_summary_partB_v2', 'setB_summary_v2'].find(name => datasets[name])
  const b = bName ? datasets[bName] : undefined
  const flags = b?.find(r => r.speaker === 'overall' && r.field === 'red_flags_caught')
  const alarms = b?.find(r => r.speaker === 'overall' && r.field === 'false_alarms')
  if (!off || !on || !flags || !alarms) throw new Error('Evaluation summaries are incomplete.')
  const ratios = [off.name_accuracy, on.name_accuracy].map(Number)
  if (ratios.some(n => !Number.isFinite(n) || n < 0 || n > 1)) throw new Error('Invalid evaluation data.')
  for (const row of [flags, alarms]) {
    if (!/^\d+$/.test(row.correct) || !/^\d+$/.test(row.total) || Number(row.total) < 1 || Number(row.correct) > Number(row.total)) throw new Error('Invalid evaluation counts.')
  }
  return { medicineOff: Math.round(ratios[0]*100), medicineOn: Math.round(ratios[1]*100), caught: `${flags.correct}/${flags.total}`, falseAlarms: `${alarms.correct}/${alarms.total}`, version: bName === 'setB_summary_partB_v2' ? 'v2 · Part B' : 'v2 · Part A' }
}
