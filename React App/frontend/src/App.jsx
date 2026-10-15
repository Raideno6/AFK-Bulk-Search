import { useEffect, useState } from 'react';
import { pink } from '@mui/material/colors';
import axios from 'axios';
import ThommyIcon from './assets/ThommyIcon.png';
import ThommyNoticingIcon from './assets/ThommyIconNoticing.png';
import BagelBoy from './assets/Jumping For Joy.gif';
import RunningSkeleton from './assets/Running.gif';
import { motion } from "motion/react";
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';

function CardCarousel({ cardName, printings, showRequestedQuantity }) {
  const [index, setIndex] = useState(0);

  if (!printings?.length) return null;

  const printing = printings[index];
  const changeSlide = (direction) => {
    setIndex((current) => (current + direction + printings.length) % printings.length);
  };

  return (
    <article className="card-carousel">
      <h2>{cardName}</h2>

      {printing.image_url && (
        <img src={printing.image_url} alt={`${cardName} — ${printing.s}`} />
      )}
        {printings.length > 1 && (
          <div className="carousel-controls">
            <button type="button" onClick={() => changeSlide(-1)} aria-label="<-">
              ‹
            </button>
            <span>{index + 1} / {printings.length}</span>
            <button type="button" onClick={() => changeSlide(1)} aria-label="->">
              ›
            </button>
          </div>
      )}

      <p>{printing.s}</p>
      <p>{String(printing.f) === '1' ? 'Foil' : 'Nonfoil'}</p>
      <p>
        Quantity: {showRequestedQuantity ? printing.requested_quantity : printing.q}
      </p>
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
  const [printImages, setPrintImages] = useState(true);
  const [showCheapestOnly, setShowCheapestOnly] = useState(false);
  const [resultsShowCheapestOnly, setResultsShowCheapestOnly] = useState(false);

  const handleChange = (event) => {
    const { checked, name } = event.target;
    if (name === 'printImages') {
      setPrintImages(checked);
    } else if (name === 'showCheapestOnly') {
      setShowCheapestOnly(checked);
    }
  };

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
      const response = await axios.post('/search', {
        text,
        printImages,
        ShowOnlyCheapest: showCheapestOnly,
      });

      console.log(response.data);
      setFoundCards(response.data.data ?? []);
      setResultsShowCheapestOnly(showCheapestOnly);
    } catch (error) {
      console.error('Search request failed:', error);
      setMessage('Could not send text to the backend.');
      setHasError(true);
    } finally {
      setIsSearching(false);
    }
  };

  const isBagelBoySearch = text.toLowerCase().includes('bagel boy');
  const isSkeletonSearch = text.toLowerCase().includes('#noticing');
  const resultPrintings = foundCards.flatMap((cardEntry) =>
    Object.values(cardEntry).flat()
  );
  const availablePrices = resultPrintings.reduce((prices, printing) => {
    const price = Number(printing.price);
    if (
      printing.price == null ||
      printing.price === '' ||
      !Number.isFinite(price)
    ) {
      return prices;
    }

    prices.push(price * Number(printing.requested_quantity ?? 1));
    return prices;
  }, []);
  const hasUnavailablePrice = availablePrices.length < resultPrintings.length;
  const totalPrice = availablePrices.reduce((total, price) => total + price, 0);
  const currencyFormatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  const formattedTotalPrice = currencyFormatter.format(totalPrice);

  const exportCheapestList = () => {
    const rows = foundCards.flatMap((cardEntry) =>
      Object.entries(cardEntry).flatMap(([cardName, printings]) =>
        printings.map((printing) => {
          const quantity = Number(printing.requested_quantity ?? 1);
          const price = Number(printing.price);
          const formattedPrice = Number.isFinite(price)
            ? currencyFormatter.format(price)
            : 'Unavailable';

          return `${cardName} - ${quantity} - ${formattedPrice}`;
        })
      )
    );
    const unavailableNote = hasUnavailablePrice
      ? '\n(Some prices are unavailable; the projected total excludes them.)'
      : '';
    const fileContent = [
      'CARD NAME - QUANTITY - PRICE',
      ...rows,
      '',
      `TOTAL PROJECTED PRICE: ${formattedTotalPrice}${unavailableNote}`,
    ].join('\n');
    const file = new Blob([fileContent], { type: 'text/plain;charset=utf-8' });
    const downloadUrl = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'cheapest-printings.txt';
    link.click();
    URL.revokeObjectURL(downloadUrl);
  };

  return (
    <div>
      <nav className="navbar">
        <div className="logo">Thommy&apos;s Terrific AFK TCG Searcher</div>
      </nav>
        {foundCards.length > 0 ? (
          <main className="found-cards">
            <div className="results-summary">
              <p>Found {foundCards.length} card{foundCards.length !== 1 ? 's' : ''}.</p>
              {resultsShowCheapestOnly && (
                <p>
                  Total price: {formattedTotalPrice}
                  {hasUnavailablePrice &&
                    ' (Some prices could not be calculated, expect actual total to be greater)'}
                </p>
              )}
            </div>
            <button type="button" onClick={() => setFoundCards([])}>
              New search
            </button>
            {resultsShowCheapestOnly && (
              <button type="button" onClick={exportCheapestList}>
                Export as text
              </button>
            )}

            <div className="card-carousel-container">
                {foundCards.flatMap((cardEntry) =>
                  Object.entries(cardEntry).map(([cardName, printings]) => (
                    <CardCarousel
                      key={cardName}
                      cardName={cardName}
                      printings={printings}
                      showRequestedQuantity={resultsShowCheapestOnly}
                    />
                  ))
                )}
            </div>
          </main>
        ) : (
        <div>
          <main className="hero">
            <h1 className="title">
              <img src={isSkeletonSearch ? ThommyNoticingIcon : ThommyIcon} alt="Thommy's Terrific AFK TCG Searcher" className="logo-image" />
            </h1>
            <p className="subtitle">Paste your MTG list below</p>
                {(isSkeletonSearch && isSearching) && (
                            <div className="skeleton-runner">
                              <motion.img
                                src={RunningSkeleton}
                                alt=""
                                style={{ width: '500px', height: 'auto', zIndex: '200', position: 'absolute', left: 0 }}
                                initial={{ x: "-100%" }}
                            animate={{
                              x: "100vw",
                            }}
                            transition={{
                              duration: 1,
                              ease: "linear",
                              repeat: Infinity,
                              repeatType: "loop"
                            }}
                            />
                          </div>
                )}
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
                      <div
                        className="bouncing-loader"
                        role="status"
                        aria-label={isBagelBoySearch ? 'Bagel Boy is searching' : 'Thommy is searching'}
                      >
                        <motion.img
                          src={isSkeletonSearch ? ThommyNoticingIcon : isBagelBoySearch ? BagelBoy : ThommyIcon}
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
                        <span className="bouncing-loader-label">
                          {isBagelBoySearch ? 'Bagel Boy is searching...' : 'Thommy is searching...'}
                        </span>
                      </div>
                    )}
                  </div>
                  <button className="search-button" type="submit" disabled={isSearching || !pricesReady}>
                    {isSearching ? 'SEARCHING...' : 'SEARCH'}
                  </button>

                  <FormGroup>
                      <FormControlLabel control={
                          <Checkbox
                          name="printImages"
                          checked={printImages}
                          onChange={handleChange}
                          sx={{
                            color: pink[800],
                            '&.Mui-checked': {
                              color: pink[600],
                            },
                          }}
                          />
                          }
                      label="Print Images"/>
                      <FormControlLabel control={
                          <Checkbox
                            name="showCheapestOnly"
                            checked={showCheapestOnly}
                            onChange={handleChange}
                            sx={{
                            color: pink[800],
                            '&.Mui-checked': {
                              color: pink[600],
                            },
                          }}/>
                        } label="Show Cheapest Only"
                       />
                  </FormGroup>

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
