import { useEffect, useState } from 'react';
import { useNavigate, Routes, Route, useParams } from 'react-router-dom';

function SearchResults() {
  const { query } = useParams();
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    setSearching(true);
    setResults([]);
    setError('');
    fetch(`/api/youtube/search?q=${encodeURIComponent(query)}`)
      .then(async r => {
        if (r.status === 401) {
          window.location.replace('/api/youtube/login');
          return { error: 'Redirecting to YouTube login...' };
        }
        return r.json();
      })
      .then(data => {
        if (data.videos) setResults(data.videos.slice(0, 10));
        else if (data.error) setError(data.error);
        setSearching(false);
      });
  }, [query]);

  const handleVideoClick = (videoId) => {
    navigate(`/youtube/video/${videoId}`);
  };

  return (
    <div style={{padding: 16}}>
      <h2 style={{textAlign: 'center'}}>Search Results</h2>
      {searching && <div>Searching...</div>}
      {error && <div style={{color: 'red', marginBottom: 12}}>{error}</div>}
      {results.length > 0 && (
        <div style={{display: 'flex', flexDirection: 'column', gap: 12}}>
          {results.map(video => (
            <div key={video.videoId} style={{display: 'flex', alignItems: 'center', background: '#222', borderRadius: 8, padding: 8, cursor: 'pointer'}} onClick={() => handleVideoClick(video.videoId)}>
              <img src={video.thumbnail} alt="thumb" style={{width: 96, height: 54, borderRadius: 6, objectFit: 'cover', marginRight: 12}} />
              <div>
                <div style={{fontWeight: 'bold'}}>{video.title}</div>
                <div style={{fontSize: 14, color: '#aaa'}}>{video.channelTitle}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function YouTube() {
  const [feed, setFeed] = useState([]);
  const [feedLoading, setFeedLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    setFeedLoading(true);
    fetch('/api/youtube/feed')
      .then(async r => {
        if (r.status === 401) {
          window.location.replace('/api/youtube/login');
          return { error: 'Redirecting to YouTube login...' };
        }
        return r.json();
      })
      .then(data => {
        if (data.feed) setFeed(data.feed);
        else if (data.error) setError(data.error);
        setFeedLoading(false);
      });
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!search.trim()) return;
    navigate(`/youtube/search/${encodeURIComponent(search)}`);
  };

  const handleVideoClick = (videoId) => {
    navigate(`/youtube/video/${videoId}`);
  };

  return (
    <Routes>
      <Route path="/" element={
        <div style={{padding: 16}}>
          <h2 style={{textAlign: 'center'}}>YouTube</h2>
          <form onSubmit={handleSearch} style={{display: 'flex', gap: 8, marginBottom: 24}}>
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search YouTube videos..."
              style={{flex: 1, padding: 8, borderRadius: 8, border: '1px solid #333', fontSize: 16}}
            />
            <button type="submit" style={{padding: '8px 16px', borderRadius: 8, background: '#c00', color: '#fff', border: 'none', fontWeight: 'bold'}}>Search</button>
          </form>
          <h3>Feed</h3>
          {feedLoading ? <div>Loading feed...</div> : (
            <div style={{display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24}}>
              {feed.map(video => (
                <div key={video.videoId} style={{display: 'flex', alignItems: 'center', background: '#222', borderRadius: 8, padding: 8, cursor: 'pointer'}} onClick={() => handleVideoClick(video.videoId)}>
                  <img src={video.thumbnail} alt="thumb" style={{width: 120, height: 68, borderRadius: 6, objectFit: 'cover', marginRight: 12}} />
                  <div>
                    <div style={{fontWeight: 'bold'}}>{video.title}</div>
                    <div style={{fontSize: 14, color: '#aaa'}}>{video.channelTitle}</div>
                    <div style={{fontSize: 12, color: '#888'}}>{new Date(video.publishedAt).toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {error && <div style={{color: 'red', marginBottom: 12}}>{error}</div>}
        </div>
      } />
      <Route path="/search/:query" element={<SearchResults />} />
    </Routes>
  );
} 