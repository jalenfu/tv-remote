import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

function formatViewCount(count) {
  if (!count) return '';
  return Number(count).toLocaleString() + ' views';
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString();
}

// Parse ISO 8601 duration (e.g., PT1H2M3S) to H:MM:SS or M:SS as appropriate.
function formatDuration(isoDuration) {
  if (!isoDuration) return '';
  const match = isoDuration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return '';
  const hours = parseInt(match[1] || '0', 10);
  const minutes = parseInt(match[2] || '0', 10);
  const seconds = parseInt(match[3] || '0', 10);
  let result = '';
  if (hours > 0) {
    result += hours + ':' + String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');
  } else {
    result += minutes + ':' + String(seconds).padStart(2, '0');
  }
  return result;
}

function YouTubeSearchResults() {
  const { query } = useParams();
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/youtube/search?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        setResults(data.videos || []);
        setLoading(false);
      });
  }, [query]);

  return (
    <div style={{padding: 24}}>
      <button onClick={() => navigate(-1)} style={{marginBottom: 16, background: '#333', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer'}}>← Back</button>
      <h2>Search results for: {query}</h2>
      {loading ? <div>Loading...</div> : (
        <ul style={{listStyle: 'none', padding: 0}}>
          {results.map(video => (
            <li key={video.videoId} style={{marginBottom: 16}}>
              <a href={`/youtube/video/${video.videoId}`} style={{color: '#fff', textDecoration: 'none'}}>
                <div style={{position: 'relative', display: 'inline-block'}}>
                  <img src={video.thumbnail} alt={video.title} style={{width: 120, verticalAlign: 'middle', borderRadius: 8}} />
                  {video.duration && (
                    <span style={{position: 'absolute', bottom: 6, right: 8, background: 'rgba(0,0,0,0.7)', color: '#fff', fontSize: 13, padding: '2px 6px', borderRadius: 4}}>
                      {formatDuration(video.duration)}
                    </span>
                  )}
                </div>
                <span style={{marginLeft: 12, fontWeight: 'bold'}}>{video.title}</span>
                <div style={{marginLeft: 132, color: '#aaa', fontSize: 14}}>{video.channelTitle}</div>
                <div style={{marginLeft: 132, color: '#aaa', fontSize: 13}}>
                  {formatViewCount(video.viewCount)}
                  {video.publishedAt && (
                    <span style={{marginLeft: 12}}>{formatDate(video.publishedAt)}</span>
                  )}
                </div>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default YouTubeSearchResults; 