import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import VolumeSlider from './components/VolumeSlider';

export default function YouTubeVideoControl() {
  const { videoId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('');
  const [volume, setVolume] = useState(0.5);
  const [seek, setSeek] = useState({ currentTime: 0, duration: 0 });
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [videoInfo, setVideoInfo] = useState(null);
  const [pollingActive, setPollingActive] = useState(false);

  // Open the video in the backend and fetch video info
  useEffect(() => {
    const lastPlayed = JSON.parse(localStorage.getItem('lastPlayedMedia') || '{}');
    let skipOpen = false;
    if (lastPlayed.type === 'youtube' && lastPlayed.videoId === videoId) {
      skipOpen = true;
    }
    const doFetch = async () => {
      if (!skipOpen) {
        setStatus('Opening video...');
        setLoading(true);
        await fetch(`/api/youtube/video/open?videoId=${videoId}`, { method: 'POST' });
      }
      // Always fetch video info
      setStatus('Loading video info...');
      setLoading(true);
      fetch(`/api/youtube/video/info?videoId=${videoId}`)
        .then(res => res.json())
        .then(data => {
          setVideoInfo(data);
          setStatus('');
          setLoading(false);
        })
        .catch(() => {
          setStatus('Failed to load video info');
          setLoading(false);
        });
      // Fetch play/pause state
      fetch(`/api/youtube/video/playing?videoId=${videoId}`)
        .then(res => res.json())
        .then(data => {
          if (typeof data.playing === 'boolean') {
            setPlaying(data.playing);
            // Save to localStorage
            const last = JSON.parse(localStorage.getItem('lastPlayedMedia') || '{}');
            if (last.type === 'youtube' && last.videoId === videoId) {
              localStorage.setItem('lastPlayedMedia', JSON.stringify({ ...last, playing: data.playing }));
            }
          }
        });
    };
    doFetch();
  }, [videoId]);

  // Fetch current system volume after video is opened and info loaded
  useEffect(() => {
    if (!pollingActive || loading || error) return;
    fetch('/api/system_volume')
      .then(r => r.json())
      .then(data => {
        if (typeof data.volume === 'number') setVolume(data.volume);
      });
  }, [pollingActive, loading, error]);

  // Save last played media to localStorage
  useEffect(() => {
    if (videoInfo) {
      localStorage.setItem('lastPlayedMedia', JSON.stringify({
        type: 'youtube',
        videoId: videoInfo.videoId,
        title: videoInfo.title,
        thumbnail: videoInfo.thumbnail,
        channelTitle: videoInfo.channelTitle
      }));
    }
  }, [videoInfo]);

  // Fetch system volume on mount
  useEffect(() => {
    fetch('/api/system_volume')
      .then(res => res.json())
      .then(data => {
        if (typeof data.volume === 'number') {
          setVolume(data.volume);
        }
      });
  }, []);

  const setSystemVolume = (v) => {
    setVolume(v);
    fetch(`/stream_volume?level=${v}`, { method: 'POST' });
  };

  // When toggling play/pause, update state and localStorage
  const handlePlayPause = () => {
    fetch(`/api/youtube/video/playpause?videoId=${videoId}`, { method: 'POST' })
      .then(() => {
        setPlaying(p => {
          const newState = !p;
          // Update localStorage
          const last = JSON.parse(localStorage.getItem('lastPlayedMedia') || '{}');
          if (last.type === 'youtube' && last.videoId === videoId) {
            localStorage.setItem('lastPlayedMedia', JSON.stringify({ ...last, playing: newState }));
          }
          return newState;
        });
      });
  };

  const handleFullscreen = () => {
    setStatus('Toggling fullscreen...');
    fetch(`/api/youtube/video/fullscreen?videoId=${encodeURIComponent(videoId)}`, {
      method: 'POST'
    })
      .then(r => r.json())
      .then(data => setStatus(data.status || data.error || ''));
  };

  const handleSeek = (t) => {
    setSeek(s => ({ ...s, currentTime: t }));
    setStatus('Seeking...');
    fetch('/api/youtube/video/seek', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ videoId, time_sec: t })
    })
      .then(r => r.json())
      .then(data => setStatus(data.status || data.error || ''));
  };

  const handleSeekRelative = (delta) => {
    setStatus(`Seeking ${delta > 0 ? '+' : ''}${delta} seconds...`);
    fetch(`/api/youtube/video/seek/relative?videoId=${encodeURIComponent(videoId)}&delta=${delta}`, {
      method: 'POST'
    })
      .then(r => r.json())
      .then(data => setStatus(data.status || data.error || ''));
  };

  return (
    <div style={{ padding: 16 }}>
      <button style={{ marginBottom: 16 }} onClick={() => navigate(-1)}>&larr; Back</button>
      <h2 style={{ textAlign: 'center' }}>YouTube Video Control</h2>
      <div style={{ textAlign: 'center', marginBottom: 16 }}>
        <b>{videoId}</b>
      </div>
      {videoInfo && (
        <div style={{background: '#222', borderRadius: 12, padding: 12, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12}}>
          <img src={videoInfo.thumbnail} alt="preview" style={{width: 96, height: 54, borderRadius: 8, objectFit: 'cover'}} />
          <div style={{flex: 1}}>
            <div style={{fontWeight: 'bold'}}>{videoInfo.title}</div>
            <div style={{fontSize: 14, color: '#aaa'}}>{videoInfo.channelTitle}</div>
            <div style={{fontSize: 12, color: '#888'}}>{new Date(videoInfo.publishedAt).toLocaleString()}</div>
          </div>
        </div>
      )}
      {loading ? <div>Loading video info...</div> : error ? (
        <div style={{ color: '#c00', textAlign: 'center' }}>{error}</div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
            <button style={{ padding: '1em', fontSize: '1.1em', borderRadius: 8, background: '#c00', color: '#fff', border: 'none' }} onClick={handlePlayPause} disabled={loading || !!error}>
              {playing ? 'Pause' : 'Play'}
            </button>
            <button style={{ padding: '1em', fontSize: '1.1em', borderRadius: 8, background: '#333', color: '#fff', border: 'none' }} onClick={handleFullscreen} disabled={loading || !!error}>
              Toggle Fullscreen
            </button>
            {/* Remove seek slider and time display, only keep skip buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button style={{ padding: '0.5em 1em', borderRadius: 8, background: '#333', color: '#fff', border: 'none' }} onClick={() => handleSeekRelative(-5)} disabled={loading || !!error}>-5s</button>
              <button style={{ padding: '0.5em 1em', borderRadius: 8, background: '#333', color: '#fff', border: 'none' }} onClick={() => handleSeekRelative(5)} disabled={loading || !!error}>+5s</button>
            </div>
            <VolumeSlider value={volume} onChange={setSystemVolume} label="System Volume" disabled={loading || !!error} />
          </div>
        </>
      )}
      {status && <div style={{ color: '#c00', textAlign: 'center' }}>{status}</div>}
    </div>
  );
} 