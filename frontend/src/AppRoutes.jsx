import { useState, useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import Twitch from './Twitch';
import TwitchStreamControl from './TwitchStreamControl';
import YouTube from './YouTube';
import YouTubeVideoControl from './YouTubeVideoControl';
import YouTubeSearchResults from './YouTubeSearchResults';

const screens = ['Home', 'Twitch', 'YouTube', 'Netflix', 'Crunchyroll'];

function MainNav({ screen, setScreen }) {
  return (
    <nav className="nav-bar">
      {screens.map(s => (
        <button
          key={s}
          className={"nav-btn" + (screen === s ? " selected" : "")}
          onClick={() => setScreen(s)}
        >
          {s}
        </button>
      ))}
    </nav>
  );
}

function HomeLastPlayedCard({ lastPlayed, onClick }) {
  if (!lastPlayed) return null;
  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onClick(); }}
      style={{
        cursor: 'pointer',
        margin: '16px auto',
        maxWidth: 320,
        background: '#222',
        borderRadius: 10,
        boxShadow: '0 2px 8px #0008',
        padding: 12,
        display: 'flex',
        alignItems: 'center'
      }}
    >
      <img src={lastPlayed.thumbnail} alt={lastPlayed.title} style={{width: 96, height: 54, borderRadius: 6, objectFit: 'cover', marginRight: 16}} />
      <div>
        <div style={{fontWeight: 'bold', fontSize: 16, color: '#fff'}}>{lastPlayed.title}</div>
        {lastPlayed.channelTitle && <div style={{color: '#aaa', fontSize: 13}}>{lastPlayed.channelTitle}</div>}
        {lastPlayed.type === 'twitch' && <div style={{color: '#9147ff', fontSize: 13}}>Twitch</div>}
        {lastPlayed.type === 'youtube' && <div style={{color: '#ff0000', fontSize: 13}}>YouTube</div>}
      </div>
    </div>
  );
}

function AudioDeviceSelector() {
  const [devices, setDevices] = useState([]);
  const [selected, setSelected] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    // Fetch devices
    fetch('/api/audio/devices')
      .then(res => res.json())
      .then(data => setDevices(data.devices || []));
    // Fetch current device
    fetch('/api/audio/currentdevice')
      .then(res => res.json())
      .then(data => {
        if (data.device && data.device.id) setSelected(data.device.id);
      });
  }, []);

  const handleChange = (e) => {
    const deviceId = e.target.value;
    setSelected(deviceId);
    setStatus('Switching device...');
    fetch('/api/audio/device', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId }),
    })
      .then(res => res.json())
      .then(data => setStatus(data.status || data.error || ''));
  };

  return (
    <div style={{margin: '16px auto', maxWidth: 320, background: '#222', borderRadius: 10, boxShadow: '0 2px 8px #0008', padding: 12}}>
      <label htmlFor="audio-device-select" style={{color: '#fff', fontWeight: 'bold'}}>Playback Device: </label>
      <select id="audio-device-select" value={selected} onChange={handleChange} style={{marginLeft: 8, padding: 4, borderRadius: 4}}>
        <option value="">Select device</option>
        {devices.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
      </select>
      {status && <div style={{color: '#6cf', marginTop: 8}}>{status}</div>}
    </div>
  );
}

function AppRoutes() {
  const [screen, setScreen] = useState('Home');
  const [lastPlayed, setLastPlayed] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // Load last played media from localStorage on every navigation
    const stored = localStorage.getItem('lastPlayedMedia');
    if (stored) setLastPlayed(JSON.parse(stored));
    else setLastPlayed(null);
  }, [location]);

  const handleLastPlayedClick = () => {
    if (!lastPlayed) return;
    if (lastPlayed.type === 'youtube') {
      navigate(`/youtube/video/${lastPlayed.videoId}`);
    } else if (lastPlayed.type === 'twitch') {
      navigate(`/twitch/${lastPlayed.channel}`);
    }
  };

  return (
    <>
      <style>{`
        body { background: #181818; }
        .app-container { max-width: 480px; margin: 0 auto; padding: 0 0 64px 0; font-family: sans-serif; background: #181818; min-height: 100vh; color: #fff; }
        .nav-bar { position: fixed; bottom: 0; left: 0; width: 100vw; background: #222; display: flex; justify-content: space-around; z-index: 100; border-top: 1px solid #333; }
        .nav-btn { flex: 1; background: none; color: #fff; border: none; border-radius: 0; padding: 1em 0; font-size: 1.1em; font-weight: bold; }
        .nav-btn.selected { background: #333; }
      `}</style>
      <div className="app-container">
        <Routes>
          <Route path="/" element={
            <>
              {screen === 'Home' && (
                <div style={{padding: 24, textAlign: 'center'}}>
                  <h1>PC TV Remote</h1>
                  <p>Select a service below.</p>
                  <AudioDeviceSelector />
                  <HomeLastPlayedCard lastPlayed={lastPlayed} onClick={handleLastPlayedClick} />
                </div>
              )}
              {screen === 'Twitch' && <Twitch navigateToStream={channel => navigate(`/twitch/${channel}`)} />}
              {screen === 'YouTube' && <YouTube />}
              {screen === 'Netflix' && <div style={{padding: 24, textAlign: 'center'}}>Netflix integration coming soon.</div>}
              {screen === 'Crunchyroll' && <div style={{padding: 24, textAlign: 'center'}}>Crunchyroll integration coming soon.</div>}
              <MainNav screen={screen} setScreen={setScreen} />
            </>
          } />
          <Route path="/twitch/:channel" element={<TwitchStreamControl />} />
          <Route path="/youtube/video/:videoId" element={<YouTubeVideoControl />} />
          <Route path="/youtube/search/:query" element={<YouTubeSearchResults />} />
        </Routes>
      </div>
    </>
  );
}

export default AppRoutes; 