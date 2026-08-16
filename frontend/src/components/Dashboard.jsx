export default function Dashboard({ onLogout }) {
  return (
    <div>
      <header style={{ padding: '16px 24px', borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600 }}>Solar & Wind Platform</span>
        <button onClick={onLogout} style={{ padding: '6px 14px', border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer', background: '#fff' }}>Logout</button>
      </header>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 53px)', color: '#999', fontSize: 18 }}>
        Frontend still on progress
      </div>
    </div>
  )
}
