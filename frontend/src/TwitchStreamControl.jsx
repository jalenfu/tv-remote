import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import VolumeSlider from './components/VolumeSlider';

const controls = [
  { label: 'Play/Pause', endpoint: '/playpause', method: 'POST' },
  { label: 'Volume Up', endpoint: '/stream_volume?direction=up', method: 'POST' },
  { label: 'Volume Down', endpoint: '/stream_volume?direction=down', method: 'POST' },
  { label: 'Mute/Unmute', endpoint: '/mute', method: 'POST' },
  { label: 'Theater Mode', endpoint: '/theater_mode', method: 'POST' },
];

export default function TwitchStreamControl() {
  const { channel } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('');
  const [stream, setStream] = useState(null);
  const [loading, setLoading] = useState(true);
  const [volume, setVolume] = useState(0.5);
  const [playing, setPlaying] = useState(true); // Assume playing by default (autoplay)

  // Open the stream in the backend and fetch stream info
  useEffect(() => {
    const lastPlayed = JSON.parse(localStorage.getItem('lastPlayedMedia') || '{}');
    let skipOpen = false;
    if (lastPlayed.type === 'twitch' && lastPlayed.channel === channel) {
      skipOpen = true;
    }
    const doFetch = async () => {
      if (!skipOpen) {
        setStatus('Opening stream...');
        await fetch(`/api/twitch_stream?channel=${encodeURIComponent(channel)}`, { method: 'POST' });
      }
      // Always fetch stream info
      setStatus('Loading stream info...');
      fetch('/api/twitch/followed')
        .then(r => r.json())
        .then(data => {
          if (data && data.streams) {
            const found = data.streams.find(s => s.user_login === channel);
            setStream(found || null);
          }
          setLoading(false);
        });
      // Fetch play/pause state
      fetch(`/api/twitch/playing?channel=${channel}`)
        .then(res => res.json())
        .then(data => {
          if (typeof data.playing === 'boolean') {
            setPlaying(data.playing);
            // Save to localStorage
            const last = JSON.parse(localStorage.getItem('lastPlayedMedia') || '{}');
            if (last.type === 'twitch' && last.channel === channel) {
              localStorage.setItem('lastPlayedMedia', JSON.stringify({ ...last, playing: data.playing }));
            }
          }
        });
    };
    doFetch();
  }, [channel]);

  // Fetch current system volume
  useEffect(() => {
    fetch('/api/audio/system_volume')
      .then(r => r.json())
      .then(data => {
        if (typeof data.volume === 'number') setVolume(data.volume);
      });
  }, []);

  // Save last played media to localStorage
  useEffect(() => {
    if (channel) {
      localStorage.setItem('lastPlayedMedia', JSON.stringify({
        type: 'twitch',
        channel: channel,
        title: channel, // Replace with stream title if available
        thumbnail: `https://static-cdn.jtvnw.net/previews-ttv/live_user_${channel}-320x180.jpg`
      }));
    }
  }, [channel]);

  const sendControl = (endpoint, method) => {
    setStatus('Sending command...');
    fetch(endpoint, { method })
      .then(r => r.json())
      .then(data => setStatus(data.status || data.error || ''));
  };

  const setSystemVolume = (v) => {
    setVolume(v);
    fetch(`/api/audio/system_volume?level=${v}`, { method: 'POST' });
  };

  // When toggling play/pause, update state and localStorage
  const handlePlayPause = () => {
    fetch(`/api/twitch/playpause?channel=${channel}`, { method: 'POST' })
      .then(() => {
        setPlaying(p => {
          const newState = !p;
          // Update localStorage
          const last = JSON.parse(localStorage.getItem('lastPlayedMedia') || '{}');
          if (last.type === 'twitch' && last.channel === channel) {
            localStorage.setItem('lastPlayedMedia', JSON.stringify({ ...last, playing: newState }));
          }
          return newState;
        });
      });
  };

  return (
    <div style={{padding: 16}}>
      <button style={{marginBottom: 16}} onClick={() => navigate(-1)}>&larr; Back</button>
      <h2 style={{textAlign: 'center'}}>Twitch Stream Control</h2>
      <div style={{textAlign: 'center', marginBottom: 16}}>
        <b>{channel}</b>
      </div>
      {loading && <div>Loading stream info...</div>}
      {stream && (
        <div style={{background: '#222', borderRadius: 12, padding: 12, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12}}>
          <img src={stream.thumbnail_url.replace('{width}', '96').replace('{height}', '54')} alt="preview" style={{width: 96, height: 54, borderRadius: 8, objectFit: 'cover'}} />
          <div style={{flex: 1}}>
            <div style={{fontWeight: 'bold'}}>{stream.user_name}</div>
            <div style={{fontSize: 14, color: '#aaa'}}>{stream.title}</div>
            <div style={{fontSize: 12, color: '#6cf'}}>{stream.viewer_count} viewers</div>
          </div>
        </div>
      )}
      <div style={{display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16}}>
        {/* Render play/pause button first, then the rest of the controls except Play/Pause and Volume */}
        <button onClick={handlePlayPause} style={{padding: '1em', fontSize: '1.1em', borderRadius: 8, background: '#333', color: '#fff', border: 'none'}}>
          {playing ? 'Pause' : 'Play'}
        </button>
        {controls.filter(ctrl => !ctrl.label.startsWith('Volume') && ctrl.label !== 'Play/Pause').map(ctrl => (
          <button key={ctrl.label} style={{padding: '1em', fontSize: '1.1em', borderRadius: 8, background: '#333', color: '#fff', border: 'none'}} onClick={() => sendControl(ctrl.endpoint, ctrl.method)}>
            {ctrl.label}
          </button>
        ))}
        <VolumeSlider value={volume} onChange={setSystemVolume} label="System Volume" />
      </div>
      {status && <div style={{color: '#6cf', textAlign: 'center'}}>{status}</div>}
    </div>
  );
} 