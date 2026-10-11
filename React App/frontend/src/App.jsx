import { useEffect, useState } from 'react';
import axios from 'axios';
import ThommyIcon from './assets/ThommyIcon.png';

export default function HomePage() {
  const [text, setText] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [message, setMessage] = useState('');
  const [hasError, setHasError] = useState(false);
  const [pricesReady, setPricesReady] = useState(false);
  const [pricesStatus, setPricesStatus] = useState('Loading card prices...');
  const [pricesLoadError, setPricesLoadError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    axios.get('/api/data')
      .then(({ data }) => {
        if (isMounted) {
          setPricesReady(true);
          setPricesStatus(`Card prices ready (${data.card_count.toLocaleString()} cards).`);
        }
      })
      .catch((error) => {
        console.error('Could not load card price data:', error);
        if (isMounted) {
          setPricesStatus('Could not load card prices. Make sure the backend is running.');
          setPricesLoadError(true);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearch = async (event) => {
    event.preventDefault();
    setIsSearching(true);
    setMessage('');
    setHasError(false);

    try {
      const response = await axios.post('/search', { text });

      console.log(response.data);
    } catch (error) {
      console.error('Search request failed:', error);
      setMessage('Could not send text to the backend. Make sure the backend is running.');
      setHasError(true);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <nav className="navbar">
        <div className="logo">Thommy&apos;s Terrific AFK TCG Searcher</div>
      </nav>

      <main className="hero">
        <h1 className="title">
          <img src={ThommyIcon} alt="Thommy's Terrific AFK TCG Searcher" className="logo-image" />
        </h1>
        <p className="subtitle">Paste your MTG list below</p>

        <form className="search-card" onSubmit={handleSearch}>
          <label className="search-label" htmlFor="search-text">
            Text to search
          </label>
          <textarea
            id="search-text"
            className="search-textarea"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Paste or type your text here..."
          />
          <button className="search-button" type="submit" disabled={isSearching || !pricesReady}>
            {isSearching ? 'SEARCHING...' : 'SEARCH'}
          </button>
          <p className={`search-message${pricesLoadError ? ' error' : ''}`} role="status">
            {pricesStatus}
          </p>
          {message && (
            <p className={`search-message${hasError ? ' error' : ''}`} role="status">
              {message}
            </p>
          )}
        </form>
      </main>
    </div>
  );
}
