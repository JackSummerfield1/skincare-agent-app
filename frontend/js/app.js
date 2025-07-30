// Minimal React application for the skincare agent frontend.
//
// This file uses React without JSX to avoid the need for a build step.  The
// React and ReactDOM libraries are provided locally via script tags in
// index.html.  The app progresses through several phases: asking the initial
// question, uploading a face photo, answering follow‑up questions, and
// displaying product recommendations.

(() => {
  const h = React.createElement;

  function App() {
    const [question, setQuestion] = React.useState('');
    const [mainAnswer, setMainAnswer] = React.useState('');
    const [phase, setPhase] = React.useState('start');
    const [file, setFile] = React.useState(null);
    const [scanResult, setScanResult] = React.useState(null);
    const [answers, setAnswers] = React.useState({});
    const [products, setProducts] = React.useState([]);

    // Fetch the initial question on first render
    React.useEffect(() => {
      fetch('/quiz/start')
        .then((res) => res.json())
        .then((data) => {
          if (data && data.question) setQuestion(data.question);
        })
        .catch((err) => {
          console.error('Failed to fetch initial question', err);
        });
    }, []);

    const handleStartSubmit = (e) => {
      e.preventDefault();
      // We simply store the user's answer but do not send it to the backend
      setPhase('scan');
    };

    const handleFileChange = (e) => {
      const f = e.target.files && e.target.files[0];
      setFile(f || null);
    };

    const handleScanSubmit = async (e) => {
      e.preventDefault();
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/scan', {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          throw new Error('Scan request failed');
        }
        const data = await res.json();
        setScanResult(data);
        // Initialise answers object
        const initAnswers = {};
        if (data && Array.isArray(data.questions)) {
          data.questions.forEach((q) => {
            initAnswers[q.id] = '';
          });
        }
        setAnswers(initAnswers);
        setPhase('followup');
      } catch (err) {
        console.error(err);
        alert('There was a problem processing your photo. Please try again.');
      }
    };

    const handleAnswerChange = (id, value) => {
      setAnswers((prev) => ({ ...prev, [id]: value }));
    };

    const handleRecommendSubmit = async (e) => {
      e.preventDefault();
      if (!scanResult) return;
      try {
        const payload = {
          issues: scanResult.issues,
          answers: answers,
        };
        const res = await fetch('/recommend', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          throw new Error('Recommendation request failed');
        }
        const data = await res.json();
        setProducts(Array.isArray(data) ? data : []);
        setPhase('results');
      } catch (err) {
        console.error(err);
        alert('Unable to fetch recommendations.');
      }
    };

    // Render dynamic follow‑up fields based on scanResult.questions
    const renderFollowupFields = () => {
      if (!scanResult || !Array.isArray(scanResult.questions)) return null;
      return scanResult.questions.map((q) => {
        // Determine field type
        if (q.type === 'select' && Array.isArray(q.options)) {
          // Build option elements including a placeholder
          const options = [
            h('option', { value: '', key: '_', disabled: true }, 'Select...'),
            ...q.options.map((opt) => h('option', { value: opt, key: opt }, opt)),
          ];
          return h(
            'div',
            { key: q.id, style: { marginBottom: '1rem' } },
            [
              h('label', { htmlFor: q.id }, q.text),
              h(
                'select',
                {
                  id: q.id,
                  value: answers[q.id] || '',
                  onChange: (e) => handleAnswerChange(q.id, e.target.value),
                  required: true,
                  style: { display: 'block', width: '100%', padding: '0.3rem', marginTop: '0.5rem' },
                },
                options,
              ),
            ],
          );
        }
        // Fallback to text/number input
        return h(
          'div',
          { key: q.id, style: { marginBottom: '1rem' } },
          [
            h('label', { htmlFor: q.id }, q.text),
            h('input', {
              id: q.id,
              type: q.type || 'text',
              value: answers[q.id] || '',
              onChange: (e) => handleAnswerChange(q.id, e.target.value),
              required: true,
              style: { display: 'block', width: '100%', padding: '0.3rem', marginTop: '0.5rem' },
            }),
          ],
        );
      });
    };

    // Render the list of product recommendations
    const renderProductCards = () => {
      if (!products || products.length === 0) {
        return h('p', null, 'No products found for the given concerns.');
      }
      return products.map((prod) => {
        return h(
          'div',
          { className: 'product-card', key: prod.id },
          [
            h('img', { src: prod.image, alt: prod.name }),
            h(
              'div',
              null,
              [
                h('h3', null, prod.name),
                h('a', { href: prod.url, target: '_blank', rel: 'noopener noreferrer' }, 'View Product'),
              ],
            ),
          ],
        );
      });
    };

    // Main render switch based on phase
    let content;
    if (phase === 'start') {
      content = h(
        'form',
        { onSubmit: handleStartSubmit },
        [
          h('p', null, question),
          h('input', {
            type: 'text',
            value: mainAnswer,
            onChange: (e) => setMainAnswer(e.target.value),
            required: true,
            style: { display: 'block', width: '100%', padding: '0.3rem', marginBottom: '1rem' },
          }),
          h('button', { type: 'submit' }, 'Next'),
        ],
      );
    } else if (phase === 'scan') {
      content = h(
        'form',
        { onSubmit: handleScanSubmit },
        [
          h('p', null, 'Upload a face photo for analysis'),
          h('input', {
            type: 'file',
            accept: 'image/*',
            onChange: handleFileChange,
            required: true,
            style: { marginBottom: '1rem' },
          }),
          h('button', { type: 'submit', disabled: !file }, 'Scan'),
        ],
      );
    } else if (phase === 'followup') {
      content = h(
        'form',
        { onSubmit: handleRecommendSubmit },
        [
          h('p', null, 'Please answer the following questions:'),
          ...renderFollowupFields(),
          h('button', { type: 'submit' }, 'Get Recommendations'),
        ],
      );
    } else if (phase === 'results') {
      content = h(
        'div',
        null,
        [
          h('h2', null, 'Recommended Products'),
          ...renderProductCards(),
        ],
      );
    } else {
      content = h('p', null, 'Loading…');
    }

    return h('div', { className: 'container' }, [h('h1', null, 'Skincare Agent'), content]);
  }

  // Render the App component at the root div
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(h(App));
})();
