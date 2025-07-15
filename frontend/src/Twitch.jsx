import { useEffect, useState } from 'react';

export default function Twitch({ navigateToStream }) {
  const [streams, setStreams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch('/api/twitch/followed')
      .then(async r => {
        if (r.status === 401) {
          const data = await r.json();
          window.location.href = data.login_url;
          return;
        }
        return r.json();
      })
      .then(data => {
        if (!data) return;
        setStreams(data.streams || []);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load streams.');
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{padding: 24}}>Loading...</div>;
  if (error) return <div style={{color: 'red', padding: 24}}>{error}</div>;

  return (
    <div style={{padding: 16}}>
      <h2 style={{textAlign: 'center'}}>Live Followed Streams</h2>
      {streams.length === 0 && <div>No live streams found.</div>}
      <div style={{display: 'flex', flexDirection: 'column', gap: 16}}>
        {streams.map(stream => (
          <div key={stream.id} style={{background: '#222', borderRadius: 12, padding: 12, display: 'flex', alignItems: 'center', gap: 12}}>
            <img src={stream.thumbnail_url.replace('{width}', '96').replace('{height}', '54')} alt="preview" style={{width: 96, height: 54, borderRadius: 8, objectFit: 'cover'}} />
            <div style={{flex: 1}}>
              <div style={{fontWeight: 'bold'}}>{stream.user_name}</div>
              <div style={{fontSize: 14, color: '#aaa'}}>{stream.title}</div>
              <div style={{fontSize: 12, color: '#6cf'}}>{stream.viewer_count} viewers</div>
            </div>
            <button style={{background: '#6441a5', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 12px', fontWeight: 'bold'}} onClick={() => navigateToStream(stream.user_login)}>
              Open
            </button>
          </div>
        ))}
      </div>
    </div>
  );
} 