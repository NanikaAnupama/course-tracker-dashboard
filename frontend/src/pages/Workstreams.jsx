import { useEffect } from 'react'
import { useApi, Loading, ErrorState, SubTabs } from '../components/ui'
import ProductionSection from '../components/ProductionSection'

export default function Workstreams({ selected = 'all', onSelect }) {
  const { data, error, loading } = useApi('/api/workstreams')
  if (loading) return <Loading />
  if (error) return <ErrorState error={error} />

  const names = data.workstreams
  if (!names.length) {
    return (
      <div className="state">
        <h3>No workstream data yet</h3>
        <p>Entries will appear here as soon as they are added to the "Content Production" sheet.</p>
      </div>
    )
  }

  return <WorkstreamsBody names={names} daily={data.daily} selected={selected} onSelect={onSelect} />
}

function WorkstreamsBody({ names, daily, selected, onSelect }) {
  const active = names.includes(selected) ? selected : names[0]

  // Keep the sidebar highlight in sync when we fall back to the first workstream.
  useEffect(() => {
    if (selected !== active) onSelect?.(active)
  }, [selected, active, onSelect])

  return (
    <>
      <SubTabs tabs={names} active={active} onChange={onSelect} />
      <ProductionSection
        key={active}
        rows={daily.filter((r) => r.workstream === active)}
        unit="items"
        totalLabel={`${active} — Total Completed`}
        emptyMsg={`No "${active}" entries in the Content Production sheet yet.`}
        showCumulative
      />
    </>
  )
}
