import { useMemo, useState } from 'react'
import { useApi, Loading, ErrorState, SubTabs } from '../components/ui'
import ProductionSection from '../components/ProductionSection'

const TABS = ['Using NotebookLM', 'Using WebTool', 'Course Page Uploading']

export default function VideoLog() {
  const [tab, setTab] = useState(TABS[0])
  const { data, error, loading } = useApi('/api/video-log')

  const nbRows = useMemo(
    () => (data?.notebooklm || []).map((r) => ({ date: r.date, person: r.person, count: r.videos })),
    [data],
  )
  const wtRows = useMemo(
    () => (data?.webtool || []).map((r) => ({ date: r.date, person: r.person, count: r.videos })),
    [data],
  )
  const cpRows = useMemo(
    () => (data?.coursePage || []).map((r) => ({ date: r.date, person: r.person, count: r.count })),
    [data],
  )

  if (loading) return <Loading />
  if (error) return <ErrorState error={error} />

  return (
    <>
      <SubTabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === TABS[0] && (
        <ProductionSection rows={nbRows} unit="videos" totalLabel="Total Videos Created"
          emptyMsg="No NotebookLM data available yet." />
      )}
      {tab === TABS[1] && (
        <ProductionSection rows={wtRows} unit="videos" totalLabel="Total Videos Produced"
          emptyMsg="No WebTool data available yet." />
      )}
      {tab === TABS[2] && (
        <ProductionSection rows={cpRows} unit="courses" totalLabel="Total Courses Uploaded" showCumulative
          emptyMsg="Daily upload counts will appear once entered in the 'Course Page Uploading Status' sheet." />
      )}
    </>
  )
}
