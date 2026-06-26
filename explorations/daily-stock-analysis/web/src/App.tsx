import { Routes, Route, Navigate } from 'react-router-dom'
import { Shell } from './components/layout/Shell'
import { Home } from './pages/Home'
import { Chat } from './pages/Chat'
import { Portfolio } from './pages/Portfolio'
import { Alerts } from './pages/Alerts'
import { DecisionSignals } from './pages/DecisionSignals'
import { Settings, History, Usage } from './pages/stubs'

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/decision-signals" element={<DecisionSignals />} />
        <Route path="/history" element={<History />} />
        <Route path="/usage" element={<Usage />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
  )
}
