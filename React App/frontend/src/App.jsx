import { useEffect, useState } from 'react';
import axios from 'axios';
import ThommyIcon from './assets/ThommyIcon.png';
import { motion } from "motion/react";

function CardCarousel({ cardName, printings }) {
  const [index, setIndex] = useState(0);

  if (!printings?.length) return null;

  const printing = printings[index];
  const changeSlide = (direction) => {
    setIndex((current) => (current + direction + printings.length) % printings.length);
  };

  return (
    <article className="card-carousel">
      <h2>{cardName}</h2>

      {printing.image_url ? (
        <img src={printing.image_url} alt={`${cardName} — ${printing.s}`} />
      ) : (
        <p>Image unavailable</p>
      )}

      <div className="carousel-controls">
        <button type="button" onClick={() => changeSlide(-1)} aria-label="<-">
          ‹
        </button>
        <span>{index + 1} / {printings.length}</span>
        <button type="button" onClick={() => changeSlide(1)} aria-label="->">
          ›
        </button>
      </div>

      <p>{printing.s}</p>
      <p>{String(printing.f) === '1' ? 'Foil' : 'Nonfoil'}</p>
      <p>Quantity: {printing.q}</p>
      <p>
        Price: {printing.price == null ? 'Unavailable' : `$${printing.price}`}
      </p>
    </article>
  );
}

export default function HomePage() {
  const [text, setText] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [message, setMessage] = useState('');
  const [hasError, setHasError] = useState(false);
  const [pricesReady, setPricesReady] = useState(false);
  const [pricesStatus, setPricesStatus] = useState('Loading card prices...');
  const [pricesLoadError, setPricesLoadError] = useState(false);
  const [foundCards, setFoundCards] = useState([]);

  useEffect(() => {
    let isMounted = true;

    axios.get('/api/data')
      .then(({ data }) => {
        if (isMounted) {
          setPricesReady(true);
        }
      })
      .catch((error) => {
        console.error('Could not load card price data:', error);
        if (isMounted) {
          setPricesStatus('Could not load card prices.');
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
      setFoundCards(response.data.data ?? []);
    } catch (error) {
      console.error('Search request failed:', error);
      setMessage('Could not send text to the backend.');
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
        {foundCards.length > 0 ? (
          <main className="found-cards">
            <button type="button" onClick={() => setFoundCards([])}>
              New search
            </button>

            <div className="card-carousel-container">
                {foundCards.flatMap((cardEntry) =>
                  Object.entries(cardEntry).map(([cardName, printings]) => (
                    <CardCarousel
                      key={cardName}
                      cardName={cardName}
                      printings={printings}
                    />
                  ))
                )}
            </div>
          </main>
        ) : (
        <div>
          <main className="hero">
            <h1 className="title">
              <img src={ThommyIcon} alt="Thommy's Terrific AFK TCG Searcher" className="logo-image" />
            </h1>
            <p className="subtitle">Paste your MTG list below</p>

                <form className="search-card" onSubmit={handleSearch}>
                  <label className="search-label" htmlFor="search-text">
                    Text to search
                  </label>
                  <div className="search-input-wrapper">
                    <textarea
                      id="search-text"
                      className="search-textarea"
                      value={text}
                      onChange={(event) => setText(event.target.value)}
                      placeholder="Paste or type your text here..."
                      disabled={isSearching}
                    />
                    {isSearching && (
                      <div className="bouncing-loader" role="status" aria-label="Thommy is searching">
                        <motion.img
                          src={ThommyIcon}
                          alt=""
                          className="bouncing-thommy"
                          animate={{
                            y: [-85, 0, 0, -10, -85, -85],
                            scaleX: [1, 0.9, 1.3, 0.85, 1, 1],
                            scaleY: [1, 1.1, 0.6, 1.15, 1, 1],
                          }}
                          transition={{
                            duration: 1.2,
                            repeat: Infinity,
                            times: [0, 0.4, 0.5, 0.55, 0.9, 1],
                            ease: ['easeIn', 'easeOut', 'easeInOut', 'easeOut', 'easeInOut'],
                          }}
                        />
                        <motion.div
                          className="bouncing-shadow"
                          aria-hidden="true"
                          animate={{
                            scale: [0.3, 0.85, 1, 0.9, 0.3, 0.3],
                            opacity: [0.2, 0.45, 0.6, 0.5, 0.2, 0.2],
                          }}
                          transition={{
                            duration: 1.2,
                            repeat: Infinity,
                            times: [0, 0.4, 0.5, 0.55, 0.9, 1],
                            ease: 'easeInOut',
                          }}
                        />
                        <span className="bouncing-loader-label">Thommy is searching...</span>
                      </div>
                    )}
                  </div>
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
      )}
    </div>
  );
}
