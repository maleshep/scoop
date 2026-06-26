import { type AnalysisReport } from '../../api/client'
import { Overview } from './Overview'
import { Strategy } from './Strategy'
import { News } from './News'
import { Details } from './Details'
import { Diagnostics } from './Diagnostics'

export function ReportSummary({ report, gaps }: { report: AnalysisReport; gaps?: any }) {
  if (report.error) {
    return <div style={{ color: '#ff6b6b', padding: 16 }}>Analysis failed: {report.error}</div>
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Overview report={report} />
      <Strategy report={report} />
      <Details report={report} />
      <News news={report.news} />
      {gaps && gaps.total > 0 && <Diagnostics gaps={gaps} />}
    </div>
  )
}
