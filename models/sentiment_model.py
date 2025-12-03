import React, { useState, useEffect, useRef } from 'react';

const SENTICA = () => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [currentSection, setCurrentSection] = useState('hero');
  const [loadingMessage, setLoadingMessage] = useState('');
  const [isVisible, setIsVisible] = useState(true);
  const [analysisData, setAnalysisData] = useState(null);
  const [availableOutputs, setAvailableOutputs] = useState([]);
  const [error, setError] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [imageStates, setImageStates] = useState({});
  const matrixRainRef = useRef(null);
  const analysisStarted = useRef(false);

  const BACKEND_URL = 'http://localhost:5000';

  const loadingMessages = [
    "Connecting to YouTube API...",
    "Fetching ALL video comments (unlimited)...",
    "Processing natural language data...",
    "Analyzing sentiment patterns...",
    "Generating sentiment visualizations...",
    "Creating word clouds...",
    "Processing author engagement data...",
    "Building temporal analysis...",
    "Computing linguistic metrics...",
    "Generating model evaluation...",
    "Creating comprehensive reports...",
    "Building interactive dashboard...",
    "Finalizing all outputs..."
  ];

  const outputCategories = {
    core: {
      title: '📂 Core Data Exports',
      description: 'Raw data in various formats',
      files: [
        { name: 'analysis.json', label: 'Raw JSON Analysis', desc: 'Complete analysis data in JSON format', icon: '📄' },
        { name: 'analysis.csv', label: 'CSV Export', desc: 'Comments with sentiment scores', icon: '📊' },
        { name: 'analysis.xlsx', label: 'Excel Spreadsheet', desc: 'Excel format for easy analysis', icon: '📈' },
        { name: 'analysis.txt', label: 'Text Dump', desc: 'Plain text export of all comments', icon: '📝' },
        { name: 'metadata.json', label: 'Video Metadata', desc: 'Video information and analysis metadata', icon: '🔍' },
        { name: 'outputs.zip', label: 'Compressed Archive', desc: 'All outputs in ZIP format', icon: '📦' }
      ]
    },
    sentiment: {
      title: '📊 Sentiment Visualizations',
      description: 'Visual analysis of comment sentiment',
      files: [
        { name: 'sentiment_bar.png', label: 'Sentiment Bar Chart', desc: 'Distribution of positive/negative/neutral', icon: '📊' },
        { name: 'sentiment_pie.png', label: 'Sentiment Pie Chart', desc: 'Percentage breakdown visualization', icon: '🥧' },
        { name: 'sentiment_ratio.csv', label: 'Sentiment Ratios', desc: 'Percentage data in CSV format', icon: '📋' },
        { name: 'avg_polarity_hist.png', label: 'Polarity Histogram', desc: 'Distribution of polarity scores', icon: '📈' },
        { name: 'avg_subjectivity_hist.png', label: 'Subjectivity Histogram', desc: 'Objectivity vs subjectivity analysis', icon: '📉' }
      ]
    },
    wordclouds: {
      title: '☁️ Word Clouds',
      description: 'Visual word frequency analysis',
      files: [
        { name: 'wordcloud.png', label: 'Overall Word Cloud', desc: 'All comments combined', icon: '☁️' },
        { name: 'positive_wordcloud.png', label: 'Positive Word Cloud', desc: 'Words from positive comments only', icon: '😊' },
        { name: 'negative_wordcloud.png', label: 'Negative Word Cloud', desc: 'Words from negative comments only', icon: '😞' },
        { name: 'neutral_wordcloud.png', label: 'Neutral Word Cloud', desc: 'Words from neutral comments only', icon: '😐' },
        { name: 'emoji_wordcloud.png', label: 'Emoji Frequency Cloud', desc: 'Most used emojis visualization', icon: '🎭' }
      ]
    },
    engagement: {
      title: '🧑 Author & Engagement Analysis',
      description: 'User engagement and activity patterns',
      files: [
        { name: 'top_authors.csv', label: 'Top Authors Data', desc: 'Most active commenters list', icon: '👥' },
        { name: 'top_authors.png', label: 'Top Authors Chart', desc: 'Visual ranking of active users', icon: '📊' },
        { name: 'top_liked_comments.csv', label: 'Most Liked Comments', desc: 'Popular comments data', icon: '❤️' },
        { name: 'top_liked_comments.png', label: 'Engagement Visualization', desc: 'Chart of most liked content', icon: '📈' },
        { name: 'engagement_stats.csv', label: 'Engagement Statistics', desc: 'Like patterns and metrics', icon: '📊' }
      ]
    },
    temporal: {
      title: '⏰ Temporal Analysis',
      description: 'Time-based comment patterns',
      files: [
        { name: 'hourly_distribution.png', label: 'Hourly Pattern', desc: 'Comments by hour of day', icon: '🕐' },
        { name: 'daily_distribution.png', label: 'Daily Pattern', desc: 'Comments by day of week', icon: '📅' },
        { name: 'monthly_distribution.png', label: 'Monthly Pattern', desc: 'Comments by month', icon: '📆' },
        { name: 'comment_timeline.png', label: 'Comment Timeline', desc: 'Cumulative comment trends', icon: '📈' },
        { name: 'engagement_timeline.png', label: 'Engagement Timeline', desc: 'Likes vs time analysis', icon: '⏱️' }
      ]
    },
    linguistic: {
      title: '🔠 Linguistic Analysis',
      description: 'Language patterns and word usage',
      files: [
        { name: 'comment_length_hist.png', label: 'Length Distribution', desc: 'Comment length patterns', icon: '📏' },
        { name: 'word_frequency.csv', label: 'Word Frequency Data', desc: 'Most common words list', icon: '📋' },
        { name: 'word_frequency.png', label: 'Word Frequency Chart', desc: 'Top words visualization', icon: '📊' },
        { name: 'bigram_frequency.csv', label: 'Bigram Analysis', desc: 'Two-word phrase patterns', icon: '🔗' },
        { name: 'bigram_frequency.png', label: 'Bigram Chart', desc: 'Common phrase visualization', icon: '📈' }
      ]
    },
    evaluation: {
      title: '🤖 Model Evaluation',
      description: 'AI model performance metrics',
      files: [
        { name: 'classification_metrics.json', label: 'Classification Metrics', desc: 'Model performance data', icon: '🎯' },
        { name: 'classification_metrics.csv', label: 'Metrics Table', desc: 'Performance metrics in CSV', icon: '📊' },
        { name: 'confusion_matrix.png', label: 'Confusion Matrix', desc: 'Classification accuracy visualization', icon: '🔍' },
        { name: 'roc_curve.png', label: 'ROC Curve', desc: 'Model performance curve', icon: '📈' },
        { name: 'pr_curve.png', label: 'Precision-Recall Curve', desc: 'PR analysis visualization', icon: '📉' }
      ]
    },
    reports: {
      title: '📑 Reports & Summaries',
      description: 'Comprehensive analysis reports',
      files: [
        { name: 'report.pdf', label: 'PDF Report', desc: 'Complete visual analysis report', icon: '📄' },
        { name: 'summary.txt', label: 'Text Summary', desc: 'Executive summary of results', icon: '📝' },
        { name: 'executive_summary.docx', label: 'Executive Summary', desc: 'Business-ready presentation', icon: '📋' },
        { name: 'dashboard.html', label: 'Interactive Dashboard', desc: 'Standalone HTML dashboard', icon: '🚀' }
      ]
    }
  };

  useEffect(() => {
    document.body.style.margin = '0';
    document.body.style.padding = '0';
    document.body.style.overflowX = 'hidden';
    document.body.style.overflowY = 'auto';

    return () => {
      document.body.style.margin = '';
      document.body.style.padding = '';
      document.body.style.overflowX = '';
      document.body.style.overflowY = '';
    };
  }, []);

  useEffect(() => {
    testBackendConnection();
  }, []);

  useEffect(() => {
    const createMatrixRain = () => {
      if (!matrixRainRef.current) return;
      const container = matrixRainRef.current;
      const chars = '01SENTICA.AI♡♢♤♧◊◈◆◇※‡†‰‱⁂⁎⁑⁕⁜⁂⚡⚠⚡⚠';

      for (let i = 0; i < 50; i++) {
        const drop = document.createElement('div');
        drop.style.cssText = `
          position: absolute;
          color: rgba(0, 212, 255, 0.1);
          font-family: 'Courier New', monospace;
          font-size: 14px;
          left: ${Math.random() * 100}%;
          animation: rain ${Math.random() * 3 + 5}s linear infinite;
          animation-delay: ${Math.random() * 5}s;
        `;
        drop.textContent = chars[Math.floor(Math.random() * chars.length)];
        container.appendChild(drop);
      }
    };

    createMatrixRain();
  }, []);

  useEffect(() => {
    if (currentSection === 'loading' && isAnalyzing) {
      let messageIndex = 0;
      const interval = setInterval(() => {
        setLoadingMessage(loadingMessages[messageIndex]);
        messageIndex = (messageIndex + 1) % loadingMessages.length;
      }, 4000);

      if (!analysisStarted.current) {
        analysisStarted.current = true;
        analyzeWithBackend();
      }

      return () => clearInterval(interval);
    }
  }, [currentSection, isAnalyzing]);

  const testBackendConnection = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/health`);
      const data = await response.json();
      console.log('Backend connection:', data);
    } catch (err) {
      console.warn('Backend connection failed:', err);
    }
  };

  const analyzeWithBackend = async (retryCount = 0) => {
    const maxRetries = 3;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000);

    try {
      console.log('Starting unlimited comment analysis...');
      setError('');

      const response = await fetch(`${BACKEND_URL}/analyze_video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_url: youtubeUrl
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('Analysis complete:', data);

      setAnalysisData(data.summary);
      setAvailableOutputs(data.outputs || []);

      setIsAnalyzing(false);
      setIsVisible(false);
      setTimeout(() => {
        setCurrentSection('results');
        setIsVisible(true);
      }, 300);

    } catch (err) {
      console.error('Analysis error:', err);
      clearTimeout(timeoutId);
      
      if (err.name === 'AbortError') {
        setError('Analysis timed out. The video might have too many comments. Please try a smaller video.');
      } else if (retryCount < maxRetries) {
        console.log(`Retrying analysis (attempt ${retryCount + 1})...`);
        await analyzeWithBackend(retryCount + 1);
        return;
      } else {
        setError(err.message || 'Analysis failed. Check your connection and try again.');
      }

      setIsAnalyzing(false);
      setIsVisible(false);
      setTimeout(() => {
        setCurrentSection('hero');
        setIsVisible(true);
      }, 300);
      analysisStarted.current = false;
    }
  };

  const handleAnalyze = () => {
    if (!youtubeUrl.trim() || !validateYouTubeURL(youtubeUrl)) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    console.log('Starting unlimited analysis for:', youtubeUrl);
    setError('');
    setIsAnalyzing(true);
    analysisStarted.current = false;
    setIsVisible(false);
    setTimeout(() => {
      setCurrentSection('loading');
      setIsVisible(true);
    }, 300);
  };

  const handleNewAnalysis = () => {
    setIsVisible(false);
    setTimeout(() => {
      setCurrentSection('hero');
      setYoutubeUrl('');
      setAnalysisData(null);
      setAvailableOutputs([]);
      setError('');
      setIsAnalyzing(false);
      setIsVisible(true);
    }, 300);
  };

  const validateYouTubeURL = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
  };

  const getImageUrl = (filename) => `${BACKEND_URL}/outputs/file/${filename}`;
  const downloadFile = (filename) => window.open(`${BACKEND_URL}/outputs/file/${filename}`, '_blank');
  const downloadAllOutputs = () => window.open(`${BACKEND_URL}/outputs/zip`, '_blank');
  const openDashboard = () => window.open(`${BACKEND_URL}/outputs/file/dashboard.html`, '_blank');

  const getAvailableFilesForCategory = (category) => {
    return category.files.filter(file => availableOutputs.includes(file.name));
  };

  const getUnavailableFilesForCategory = (category) => {
    return category.files.filter(file => !availableOutputs.includes(file.name));
  };

  const containerStyle = {
    fontFamily: 'Inter, sans-serif',
    background: 'linear-gradient(135deg, #0a0e27 0%, #1a1f3a 30%, #2d1b69 60%, #1e1b4b 100%)',
    color: '#ffffff',
    minHeight: '100vh',
    width: '100vw',
    position: 'relative',
    overflowX: 'hidden'
  };

  const heroSectionStyle = {
    minHeight: '100vh',
    display: currentSection === 'hero' ? 'flex' : 'none',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
    textAlign: 'center',
    opacity: currentSection === 'hero' && isVisible ? 1 : 0,
    transform: currentSection === 'hero' && isVisible ? 'translateY(0)' : 'translateY(20px)',
    transition: 'all 0.6s ease'
  };

  const loadingSectionStyle = {
    minHeight: '100vh',
    display: currentSection === 'loading' ? 'flex' : 'none',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    opacity: currentSection === 'loading' && isVisible ? 1 : 0,
    transform: currentSection === 'loading' && isVisible ? 'translateY(0)' : 'translateY(20px)',
    transition: 'all 0.6s ease'
  };

  const resultsSectionStyle = {
    minHeight: '100vh',
    width: '100%',
    padding: '2rem',
    boxSizing: 'border-box',
    display: currentSection === 'results' ? 'block' : 'none',
    opacity: currentSection === 'results' && isVisible ? 1 : 0,
    transform: currentSection === 'results' && isVisible ? 'translateY(0)' : 'translateY(20px)',
    transition: 'all 0.6s ease'
  };

  const titleStyle = {
    fontSize: 'clamp(3rem, 8vw, 8rem)',
    fontWeight: 900,
    background: 'linear-gradient(45deg, #00d4ff, #7b2cbf, #ff006e, #00d4ff)',
    backgroundSize: '400% 400%',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    marginBottom: '1rem',
    textShadow: '0 0 50px rgba(0, 212, 255, 0.5)'
  };

  const buttonStyle = {
    width: '100%',
    padding: '1.2rem 2rem',
    fontSize: '1.2rem',
    fontWeight: 600,
    background: 'linear-gradient(45deg, #00d4ff, #7b2cbf)',
    border: 'none',
    borderRadius: '15px',
    color: 'white',
    cursor: !youtubeUrl.trim() || !validateYouTubeURL(youtubeUrl) || isAnalyzing ? 'not-allowed' : 'pointer',
    transition: 'all 0.3s ease',
    opacity: !youtubeUrl.trim() || !validateYouTubeURL(youtubeUrl) || isAnalyzing ? 0.6 : 1
  };

  return (
    <div style={containerStyle}>
      <style>
        {`
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
          @keyframes rain { 0% { transform: translateY(-100vh); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateY(100vh); opacity: 0; } }
          @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
          @keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }
          @keyframes loadingProgress { 0% { width: 0%; } 25% { width: 30%; } 50% { width: 60%; } 75% { width: 85%; } 100% { width: 100%; } }
          @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-10px); } 75% { transform: translateX(10px); } }
        `}
      </style>

      {/* Matrix Rain Effect */}
      <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: -1, overflow: 'hidden' }} ref={matrixRainRef}></div>

      {/* Hero Section */}
      <div style={heroSectionStyle}>
        <h1 style={titleStyle}>SENTICA</h1>
        <div style={{ fontSize: 'clamp(1.2rem, 3vw, 2rem)', color: '#b8c5d1', marginBottom: '1rem' }}>
          Advanced YouTube Sentiment Analyzer
        </div>
        <p style={{ fontSize: 'clamp(1rem, 2vw, 1.2rem)', color: '#8892b0', maxWidth: '600px', lineHeight: 1.6, marginBottom: '3rem' }}>
          Analyze unlimited YouTube comments with AI-powered sentiment analysis. Generate 40+ comprehensive outputs including visualizations, reports, temporal analysis, and engagement metrics.
        </p>

        <div style={{ maxWidth: '600px', width: '100%', marginBottom: '3rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(20px)', borderRadius: '20px', padding: '2rem' }}>
            <input
              type="text"
              style={{
                width: '100%',
                padding: '1rem 1.5rem',
                fontSize: '1.1rem',
                background: 'rgba(255, 255, 255, 0.1)',
                border: `2px solid ${youtubeUrl ? (validateYouTubeURL(youtubeUrl) ? '#22c55e' : '#ff006e') : 'rgba(255, 255, 255, 0.2)'}`,
                borderRadius: '15px',
                color: '#ffffff',
                outline: 'none',
                marginBottom: '1.5rem',
                fontFamily: 'Inter, sans-serif'
              }}
              placeholder="Enter YouTube video URL (e.g., https://youtube.com/watch?v=...)"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            {error && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '10px', padding: '1rem', margin: '1rem 0', color: '#fca5a5', textAlign: 'center' }}>
                {error}
              </div>
            )}
            <button style={buttonStyle} onClick={handleAnalyze} disabled={!youtubeUrl.trim() || !validateYouTubeURL(youtubeUrl) || isAnalyzing}>
              {isAnalyzing ? 'Analyzing All Comments...' : 'Analyze All Comments (Unlimited)'}
            </button>
          </div>
        </div>
      </div>

      {/* Loading Section */}
      <div style={loadingSectionStyle}>
        <div style={{ width: '120px', height: '120px', border: '4px solid rgba(0, 212, 255, 0.2)', borderTop: '4px solid #00d4ff', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '2rem' }}></div>
        <div style={{ fontSize: '1.5rem', color: '#00d4ff', marginBottom: '1rem', animation: 'pulse 1.5s ease-in-out infinite' }}>
          Analyzing ALL Comments...
        </div>
        <div style={{ width: '80%', maxWidth: '400px', height: '4px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '2px', margin: '1rem 0', overflow: 'hidden' }}>
          <div style={{ height: '100%', background: 'linear-gradient(90deg, #00d4ff, #7b2cbf)', borderRadius: '2px', animation: 'loadingProgress 15s ease-in-out infinite' }}></div>
        </div>
        <p style={{ color: '#8892b0', fontSize: '1rem', marginBottom: '1rem' }}>{loadingMessage}</p>
        <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>Processing unlimited comments and generating comprehensive analysis...</p>
      </div>

      {/* Results Section */}
      <div style={resultsSectionStyle}>
        <button 
          style={{ position: 'fixed', top: '2rem', right: '2rem', padding: '0.8rem 1.5rem', background: 'rgba(255, 255, 255, 0.1)', border: '1px solid rgba(255, 255, 255, 0.2)', borderRadius: '25px', color: '#ffffff', cursor: 'pointer', zIndex: 1000 }}
          onClick={handleNewAnalysis}
        >
          + New Analysis
        </button>

        <div style={{ textAlign: 'center', marginBottom: '3rem', paddingTop: '5rem' }}>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 800, background: 'linear-gradient(45deg, #00d4ff, #7b2cbf)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '0.5rem' }}>
            Comprehensive Analysis Complete
          </h2>
          <p style={{ color: '#8892b0', fontSize: '1.1rem' }}>
            {analysisData && analysisData.title ? `Analysis for: ${analysisData.title}` : 'Complete unlimited comment analysis results'}
          </p>
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginBottom: '3rem', flexWrap: 'wrap' }}>
          <button 
            style={{ background: 'linear-gradient(45deg, #3b82f6, #1d4ed8)', border: 'none', borderRadius: '25px', color: 'white', padding: '1.2rem 2.5rem', cursor: 'pointer', fontWeight: 600, fontSize: '1.1rem' }}
            onClick={downloadAllOutputs}
          >
            📦 Download Complete Package (ZIP)
          </button>
          {availableOutputs.includes('dashboard.html') && (
            <button 
              style={{ background: 'linear-gradient(45deg, #7b2cbf, #5a1a7b)', border: 'none', borderRadius: '25px', color: 'white', padding: '1rem 2rem', cursor: 'pointer', fontWeight: 600 }}
              onClick={openDashboard}
            >
              🚀 Open Interactive Dashboard
            </button>
          )}
          {availableOutputs.includes('report.pdf') && (
            <button 
              style={{ background: 'linear-gradient(45deg, #22c55e, #16a34a)', border: 'none', borderRadius: '25px', color: 'white', padding: '1rem 2rem', cursor: 'pointer', fontWeight: 600 }}
              onClick={() => downloadFile('report.pdf')}
            >
              📄 Download PDF Report
            </button>
          )}
        </div>

        {/* Summary */}
        {availableOutputs.length > 0 && (
          <div style={{ textAlign: 'center', color: '#6b7280', fontSize: '0.9rem', marginTop: '2rem', padding: '2rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '15px' }}>
            <h4 style={{ color: '#00d4ff', marginBottom: '1rem' }}>Analysis Summary</h4>
            <p>
              Successfully generated <strong>{availableOutputs.length}</strong> comprehensive output files from{' '}
              <strong>{analysisData && analysisData.total_comments ? analysisData.total_comments.toLocaleString() : '0'}</strong> comments.
            </p>
            <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', opacity: '0.8' }}>
              All files include data exports, visualizations, temporal analysis, linguistic metrics, engagement patterns, and comprehensive reports ready for download.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SENTICA;












import React, { useState, useEffect, useRef } from 'react';

const SENTICA = () => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [currentSection, setCurrentSection] = useState('hero');
  const [loadingMessage, setLoadingMessage] = useState('');
  const [isVisible, setIsVisible] = useState(true);
  const [analysisData, setAnalysisData] = useState(null);
  const [availableOutputs, setAvailableOutputs] = useState([]);
  const [error, setError] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [progress, setProgress] = useState(0);
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const analysisStarted = useRef(false);

  const BACKEND_URL = 'http://localhost:5000';

  const loadingMessages = [
    "Connecting to YouTube API...",
    "Fetching ALL video comments (unlimited)...",
    "Processing natural language data...",
    "Analyzing sentiment patterns...",
    "Generating sentiment visualizations...",
    "Creating word clouds...",
    "Processing author engagement data...",
    "Building temporal analysis...",
    "Computing linguistic metrics...",
    "Generating model evaluation...",
    "Creating comprehensive reports...",
    "Building interactive dashboard...",
    "Finalizing all outputs..."
  ];

  const outputCategories = {
    core: {
      title: 'Core Data Exports',
      icon: '📂',
      color: '#3b82f6',
      files: [
        { name: 'analysis.json', label: 'JSON Analysis', icon: '📄' },
        { name: 'analysis.csv', label: 'CSV Export', icon: '📊' },
        { name: 'analysis.xlsx', label: 'Excel Sheet', icon: '📈' },
        { name: 'analysis.txt', label: 'Text Dump', icon: '📝' },
        { name: 'metadata.json', label: 'Metadata', icon: '🔍' },
        { name: 'outputs.zip', label: 'ZIP Archive', icon: '📦' }
      ]
    },
    sentiment: {
      title: 'Sentiment Visualizations',
      icon: '📊',
      color: '#8b5cf6',
      files: [
        { name: 'sentiment_bar.png', label: 'Bar Chart', icon: '📊' },
        { name: 'sentiment_pie.png', label: 'Pie Chart', icon: '🥧' },
        { name: 'sentiment_ratio.csv', label: 'Ratios', icon: '📋' },
        { name: 'avg_polarity_hist.png', label: 'Polarity', icon: '📈' },
        { name: 'avg_subjectivity_hist.png', label: 'Subjectivity', icon: '📉' }
      ]
    },
    wordclouds: {
      title: 'Word Clouds',
      icon: '☁️',
      color: '#ec4899',
      files: [
        { name: 'wordcloud.png', label: 'Overall', icon: '☁️' },
        { name: 'positive_wordcloud.png', label: 'Positive', icon: '😊' },
        { name: 'negative_wordcloud.png', label: 'Negative', icon: '😞' },
        { name: 'neutral_wordcloud.png', label: 'Neutral', icon: '😐' },
        { name: 'emoji_wordcloud.png', label: 'Emoji', icon: '🎭' }
      ]
    },
    engagement: {
      title: 'Engagement Analysis',
      icon: '🧑',
      color: '#f59e0b',
      files: [
        { name: 'top_authors.csv', label: 'Top Authors', icon: '👥' },
        { name: 'top_authors.png', label: 'Authors Chart', icon: '📊' },
        { name: 'top_liked_comments.csv', label: 'Liked Comments', icon: '❤️' },
        { name: 'top_liked_comments.png', label: 'Engagement Chart', icon: '📈' },
        { name: 'engagement_stats.csv', label: 'Stats', icon: '📊' }
      ]
    },
    temporal: {
      title: 'Temporal Analysis',
      icon: '⏰',
      color: '#10b981',
      files: [
        { name: 'hourly_distribution.png', label: 'Hourly', icon: '🕐' },
        { name: 'daily_distribution.png', label: 'Daily', icon: '📅' },
        { name: 'monthly_distribution.png', label: 'Monthly', icon: '📆' },
        { name: 'comment_timeline.png', label: 'Timeline', icon: '📈' },
        { name: 'engagement_timeline.png', label: 'Engagement', icon: '⏱️' }
      ]
    },
    linguistic: {
      title: 'Linguistic Analysis',
      icon: '🔠',
      color: '#06b6d4',
      files: [
        { name: 'comment_length_hist.png', label: 'Length', icon: '📏' },
        { name: 'word_frequency.csv', label: 'Words Data', icon: '📋' },
        { name: 'word_frequency.png', label: 'Words Chart', icon: '📊' },
        { name: 'bigram_frequency.csv', label: 'Bigrams', icon: '🔗' },
        { name: 'bigram_frequency.png', label: 'Bigram Chart', icon: '📈' }
      ]
    },
    evaluation: {
      title: 'Model Evaluation',
      icon: '🤖',
      color: '#6366f1',
      files: [
        { name: 'classification_metrics.json', label: 'Metrics', icon: '🎯' },
        { name: 'classification_metrics.csv', label: 'Metrics Table', icon: '📊' },
        { name: 'confusion_matrix.png', label: 'Confusion Matrix', icon: '🔍' },
        { name: 'roc_curve.png', label: 'ROC Curve', icon: '📈' },
        { name: 'pr_curve.png', label: 'PR Curve', icon: '📉' }
      ]
    },
    reports: {
      title: 'Reports & Summaries',
      icon: '📑',
      color: '#14b8a6',
      files: [
        { name: 'report.pdf', label: 'PDF Report', icon: '📄' },
        { name: 'summary.txt', label: 'Summary', icon: '📝' },
        { name: 'executive_summary.docx', label: 'Executive', icon: '📋' },
        { name: 'dashboard.html', label: 'Dashboard', icon: '🚀' }
      ]
    }
  };

  // Particle system for canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.radius = Math.random() * 2 + 1;
        this.opacity = Math.random() * 0.5 + 0.2;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 212, 255, ${this.opacity})`;
        ctx.fill();
      }
    }

    for (let i = 0; i < 100; i++) {
      particlesRef.current.push(new Particle());
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      particlesRef.current.forEach((particle, i) => {
        particle.update();
        particle.draw();

        particlesRef.current.slice(i + 1).forEach(other => {
          const dx = particle.x - other.x;
          const dy = particle.y - other.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 100) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(0, 212, 255, ${0.2 * (1 - dist / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          }
        });
      });

      requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Mouse tracking
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Backend connection test
  useEffect(() => {
    const testBackendConnection = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/health`);
        const data = await response.json();
        console.log('Backend connection:', data);
      } catch (err) {
        console.warn('Backend connection failed:', err);
      }
    };
    testBackendConnection();
  }, []);

  // Loading progress simulation
  useEffect(() => {
    if (currentSection === 'loading' && isAnalyzing) {
      let messageIndex = 0;
      let progressValue = 0;

      const messageInterval = setInterval(() => {
        setLoadingMessage(loadingMessages[messageIndex]);
        messageIndex = (messageIndex + 1) % loadingMessages.length;
      }, 4000);

      const progressInterval = setInterval(() => {
        progressValue += Math.random() * 5;
        if (progressValue > 95) progressValue = 95;
        setProgress(progressValue);
      }, 500);

      if (!analysisStarted.current) {
        analysisStarted.current = true;
        analyzeWithBackend();
      }

      return () => {
        clearInterval(messageInterval);
        clearInterval(progressInterval);
      };
    }
  }, [currentSection, isAnalyzing]);

  const analyzeWithBackend = async (retryCount = 0) => {
    const maxRetries = 3;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000);

    try {
      setError('');
      const response = await fetch(`${BACKEND_URL}/analyze_video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_url: youtubeUrl }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setAnalysisData(data.summary);
      setAvailableOutputs(data.outputs || []);
      setProgress(100);

      setTimeout(() => {
        setIsAnalyzing(false);
        setIsVisible(false);
        setTimeout(() => {
          setCurrentSection('results');
          setIsVisible(true);
        }, 300);
      }, 1000);

    } catch (err) {
      clearTimeout(timeoutId);
      
      if (err.name === 'AbortError') {
        setError('Analysis timed out. Try a smaller video.');
      } else if (retryCount < maxRetries) {
        await analyzeWithBackend(retryCount + 1);
        return;
      } else {
        setError(err.message || 'Analysis failed.');
      }

      setIsAnalyzing(false);
      setIsVisible(false);
      setTimeout(() => {
        setCurrentSection('hero');
        setIsVisible(true);
      }, 300);
      analysisStarted.current = false;
    }
  };

  const handleAnalyze = () => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    if (!youtubeUrl.trim() || !youtubeRegex.test(youtubeUrl)) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    setError('');
    setIsAnalyzing(true);
    setProgress(0);
    analysisStarted.current = false;
    setIsVisible(false);
    setTimeout(() => {
      setCurrentSection('loading');
      setIsVisible(true);
    }, 300);
  };

  const handleNewAnalysis = () => {
    setIsVisible(false);
    setTimeout(() => {
      setCurrentSection('hero');
      setYoutubeUrl('');
      setAnalysisData(null);
      setAvailableOutputs([]);
      setError('');
      setIsAnalyzing(false);
      setSelectedCategory(null);
      setIsVisible(true);
    }, 300);
  };

  const downloadFile = (filename) => window.open(`${BACKEND_URL}/outputs/file/${filename}`, '_blank');
  const downloadAllOutputs = () => window.open(`${BACKEND_URL}/outputs/zip`, '_blank');

  return (
    <div style={{
      fontFamily: "'Inter', sans-serif",
      background: 'linear-gradient(135deg, #0a0e27 0%, #1a1f3a 30%, #2d1b69 60%, #1e1b4b 100%)',
      color: '#ffffff',
      minHeight: '100vh',
      width: '100vw',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Orbitron:wght@400;500;600;700;800;900&display=swap');
        
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(5deg); }
        }
        
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.5), 0 0 40px rgba(123, 44, 191, 0.3); }
          50% { box-shadow: 0 0 40px rgba(0, 212, 255, 0.8), 0 0 80px rgba(123, 44, 191, 0.5); }
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.05); }
        }
        
        @keyframes slideIn {
          from { transform: translateX(-100px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.9); }
          to { opacity: 1; transform: scale(1); }
        }
        
        @keyframes shimmer {
          0% { background-position: -1000px 0; }
          100% { background-position: 1000px 0; }
        }
        
        .glass {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .glass:hover {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(0, 212, 255, 0.3);
          transform: translateY(-5px);
          transition: all 0.3s ease;
        }
        
        .neon-text {
          text-shadow: 0 0 10px rgba(0, 212, 255, 0.8),
                       0 0 20px rgba(0, 212, 255, 0.6),
                       0 0 30px rgba(123, 44, 191, 0.4);
        }
        
        .card-3d {
          transform-style: preserve-3d;
          transition: transform 0.3s ease;
        }
        
        .card-3d:hover {
          transform: rotateX(5deg) rotateY(5deg) translateZ(10px);
        }
      `}</style>

      <canvas ref={canvasRef} style={{ position: 'fixed', top: 0, left: 0, zIndex: 0, pointerEvents: 'none' }} />

      <div style={{
        position: 'fixed',
        left: mousePosition.x - 250,
        top: mousePosition.y - 250,
        width: '500px',
        height: '500px',
        background: 'radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 70%)',
        pointerEvents: 'none',
        zIndex: 1,
        transition: 'all 0.1s ease'
      }} />

      {currentSection === 'hero' && (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          position: 'relative',
          zIndex: 2,
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'scale(1)' : 'scale(0.95)',
          transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)'
        }}>
          <div style={{ animation: 'float 6s ease-in-out infinite' }}>
            <h1 className="neon-text" style={{
              fontFamily: "'Orbitron', sans-serif",
              fontSize: 'clamp(4rem, 12vw, 10rem)',
              fontWeight: 900,
              background: 'linear-gradient(45deg, #00d4ff, #7b2cbf, #ff006e, #00d4ff)',
              backgroundSize: '300% 300%',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: '1rem',
              animation: 'shimmer 3s infinite linear',
              letterSpacing: '0.1em'
            }}>
              SENTICA
            </h1>
          </div>

          <div style={{
            fontSize: 'clamp(1.2rem, 3vw, 2.5rem)',
            fontWeight: 600,
            background: 'linear-gradient(90deg, #00d4ff, #ffffff)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '2rem',
            animation: 'pulse 2s ease-in-out infinite'
          }}>
            AI-Powered Sentiment Analysis Engine
          </div>

          <p style={{
            fontSize: 'clamp(1rem, 2vw, 1.3rem)',
            color: '#b8c5d1',
            maxWidth: '700px',
            lineHeight: 1.8,
            textAlign: 'center',
            marginBottom: '3rem'
          }}>
            Harness unlimited YouTube comment analysis with cutting-edge AI. Generate 40+ comprehensive outputs including advanced visualizations, temporal patterns, and deep engagement metrics.
          </p>

          <div className="glass" style={{
            maxWidth: '700px',
            width: '100%',
            padding: '3rem',
            borderRadius: '30px',
            animation: 'glow 3s ease-in-out infinite'
          }}>
            <input
              type="text"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder="Enter YouTube URL..."
              style={{
                width: '100%',
                padding: '1.5rem 2rem',
                fontSize: '1.2rem',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '2px solid rgba(0, 212, 255, 0.3)',
                borderRadius: '20px',
                color: '#ffffff',
                outline: 'none',
                marginBottom: '2rem',
                transition: 'all 0.3s ease'
              }}
            />

            {error && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
                borderRadius: '15px',
                padding: '1rem',
                marginBottom: '1.5rem',
                color: '#fca5a5',
                textAlign: 'center',
                animation: 'fadeIn 0.3s ease'
              }}>
                {error}
              </div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              style={{
                width: '100%',
                padding: '1.5rem 2rem',
                fontSize: '1.3rem',
                fontWeight: 700,
                background: 'linear-gradient(45deg, #00d4ff, #7b2cbf)',
                border: 'none',
                borderRadius: '20px',
                color: 'white',
                cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                opacity: isAnalyzing ? 0.6 : 1,
                transition: 'all 0.3s ease',
                boxShadow: '0 10px 30px rgba(0, 212, 255, 0.3)'
              }}
            >
              {isAnalyzing ? 'ANALYZING...' : '🚀 ANALYZE UNLIMITED COMMENTS'}
            </button>
          </div>
        </div>
      )}

      {currentSection === 'loading' && (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          zIndex: 2,
          opacity: isVisible ? 1 : 0,
          transition: 'opacity 0.6s ease'
        }}>
          <div style={{
            width: '150px',
            height: '150px',
            position: 'relative',
            animation: 'float 3s ease-in-out infinite',
            marginBottom: '3rem'
          }}>
            <div style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              border: '3px solid rgba(0, 212, 255, 0.5)',
              borderRadius: '20px',
              animation: 'pulse 2s ease-in-out infinite',
              boxShadow: '0 0 40px rgba(0, 212, 255, 0.6)'
            }} />
          </div>

          <h2 className="neon-text" style={{
            fontSize: '2.5rem',
            fontWeight: 800,
            marginBottom: '2rem',
            animation: 'pulse 2s ease-in-out infinite'
          }}>
            PROCESSING DATA
          </h2>

          <div style={{
            width: '80%',
            maxWidth: '600px',
            height: '8px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '10px',
            overflow: 'hidden',
            marginBottom: '2rem'
          }}>
            <div style={{
              width: `${progress}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #00d4ff, #7b2cbf, #ff006e)',
              borderRadius: '10px',
              transition: 'width 0.5s ease',
              boxShadow: '0 0 20px rgba(0, 212, 255, 0.8)'
            }} />
          </div>

          <div style={{
            fontSize: '1.5rem',
            color: '#00d4ff',
            marginBottom: '1rem',
            fontWeight: 600
          }}>
            {Math.round(progress)}%
          </div>

          <p style={{
            fontSize: '1.2rem',
            color: '#8892b0',
            textAlign: 'center',
            maxWidth: '600px'
          }}>
            {loadingMessage}
          </p>

          <div style={{
            marginTop: '2rem',
            fontSize: '0.9rem',
            color: '#6b7280',
            textAlign: 'center'
          }}>
            Analyzing unlimited comments • Generating 40+ outputs
          </div>
        </div>
      )}

      {currentSection === 'results' && (
        <div style={{
          minHeight: '100vh',
          width: '100%',
          padding: '2rem',
          position: 'relative',
          zIndex: 2,
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.6s ease'
        }}>
          <button
            onClick={handleNewAnalysis}
            className="glass"
            style={{
              position: 'fixed',
              top: '2rem',
              right: '2rem',
              padding: '1rem 2rem',
              borderRadius: '30px',
              cursor: 'pointer',
              zIndex: 1000,
              fontWeight: 600,
              fontSize: '1rem',
              color: '#00d4ff',
              border: 'none'
            }}
          >
            ✨ NEW ANALYSIS
          </button>

          <div style={{ textAlign: 'center', marginBottom: '4rem', paddingTop: '5rem' }}>
            <h2 className="neon-text" style={{
              fontFamily: "'Orbitron', sans-serif",
              fontSize: 'clamp(2rem, 5vw, 4rem)',
              fontWeight: 900,
              marginBottom: '1rem'
            }}>
              ANALYSIS COMPLETE
            </h2>
            <p style={{
              fontSize: '1.3rem',
              color: '#8892b0',
              maxWidth: '800px',
              margin: '0 auto'
            }}>
              {analysisData && analysisData.title ? analysisData.title : 'Comprehensive Results Ready'}
            </p>
          </div>

          {analysisData && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '2rem',
              maxWidth: '1400px',
              margin: '0 auto 4rem',
              animation: 'fadeIn 0.6s ease'
            }}>
              {[
                { label: 'Total Comments', value: analysisData.total_comments ? analysisData.total_comments.toLocaleString() : '0', color: '#3b82f6' },
                { label: 'Positive', value: `${analysisData.pos} (${((analysisData.pos/analysisData.total_comments)*100).toFixed(1)}%)`, color: '#10b981' },
                { label: 'Negative', value: `${analysisData.neg} (${((analysisData.neg/analysisData.total_comments)*100).toFixed(1)}%)`, color: '#ef4444' },
                { label: 'Neutral', value: `${analysisData.neu} (${((analysisData.neu/analysisData.total_comments)*100).toFixed(1)}%)`, color: '#8b5cf6' },
                { label: 'Avg Polarity', value: analysisData.avg_polarity ? analysisData.avg_polarity.toFixed(3) : '0.000', color: '#00d4ff' }
              ].map((stat, i) => (
                <div key={i} className="glass card-3d" style={{
                  padding: '2rem',
                  borderRadius: '25px',
                  textAlign: 'center',
                  animation: `slideIn 0.6s ease ${i * 0.1}s backwards`
                }}>
                  <div style={{
                    fontSize: '3rem',
                    fontWeight: 900,
                    color: stat.color,
                    marginBottom: '0.5rem'
                  }}>
                    {stat.value}
                  </div>
                  <div style={{
                    fontSize: '1rem',
                    color: '#8892b0',
                    fontWeight: 600
                  }}>
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{
            display: 'flex',
            gap: '1.5rem',
            justifyContent: 'center',
            marginBottom: '4rem',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={downloadAllOutputs}
              className="glass"
              style={{
                padding: '1.5rem 3rem',
                borderRadius: '25px',
                fontSize: '1.2rem',
                fontWeight: 700,
                cursor: 'pointer',
                background: 'linear-gradient(45deg, #3b82f6, #1d4ed8)',
                border: 'none',
                color: 'white',
                boxShadow: '0 10px 40px rgba(59, 130, 246, 0.4)',
                animation: 'fadeIn 0.8s ease'
              }}
            >
              📦 DOWNLOAD ALL (ZIP)
            </button>

            {availableOutputs.includes('dashboard.html') && (
              <button
                onClick={() => window.open(`${BACKEND_URL}/outputs/file/dashboard.html`, '_blank')}
                className="glass"
                style={{
                  padding: '1.5rem 3rem',
                  borderRadius: '25px',
                  fontSize: '1.2rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  background: 'linear-gradient(45deg, #7b2cbf, #5a1a7b)',
                  border: 'none',
                  color: 'white',
                  boxShadow: '0 10px 40px rgba(123, 44, 191, 0.4)',
                  animation: 'fadeIn 0.9s ease'
                }}
              >
                🚀 DASHBOARD
              </button>
            )}

            {availableOutputs.includes('report.pdf') && (
              <button
                onClick={() => downloadFile('report.pdf')}
                className="glass"
                style={{
                  padding: '1.5rem 3rem',
                  borderRadius: '25px',
                  fontSize: '1.2rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  background: 'linear-gradient(45deg, #10b981, #059669)',
                  border: 'none',
                  color: 'white',
                  boxShadow: '0 10px 40px rgba(16, 185, 129, 0.4)',
                  animation: 'fadeIn 1s ease'
                }}
              >
                📄 PDF REPORT
              </button>
            )}
          </div>

          <div style={{
            maxWidth: '1600px',
            margin: '0 auto'
          }}>
            <h3 style={{
              fontSize: '2rem',
              fontWeight: 800,
              textAlign: 'center',
              marginBottom: '3rem',
              background: 'linear-gradient(90deg, #00d4ff, #7b2cbf)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              OUTPUT CATEGORIES
            </h3>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
              gap: '2rem'
            }}>
              {Object.entries(outputCategories).map(([key, category], index) => {
                const availableFiles = category.files.filter(f => availableOutputs.includes(f.name));
                
                return (
                  <div
                    key={key}
                    className="glass card-3d"
                    onClick={() => setSelectedCategory(selectedCategory === key ? null : key)}
                    style={{
                      padding: '2rem',
                      borderRadius: '25px',
                      cursor: 'pointer',
                      animation: `fadeIn 0.6s ease ${index * 0.1}s backwards`,
                      borderLeft: `4px solid ${category.color}`,
                      position: 'relative',
                      overflow: 'hidden'
                    }}
                  >
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      background: `linear-gradient(135deg, ${category.color}15, transparent)`,
                      pointerEvents: 'none'
                    }} />

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '1.5rem',
                      position: 'relative'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{
                          fontSize: '2.5rem',
                          filter: 'drop-shadow(0 0 10px rgba(0, 212, 255, 0.5))'
                        }}>
                          {category.icon}
                        </div>
                        <div>
                          <h4 style={{
                            fontSize: '1.3rem',
                            fontWeight: 700,
                            color: category.color,
                            margin: 0
                          }}>
                            {category.title}
                          </h4>
                          <div style={{
                            fontSize: '0.9rem',
                            color: '#8892b0',
                            marginTop: '0.3rem'
                          }}>
                            {availableFiles.length} / {category.files.length} files
                          </div>
                        </div>
                      </div>

                      <div style={{
                        fontSize: '1.5rem',
                        color: '#00d4ff',
                        transform: selectedCategory === key ? 'rotate(180deg)' : 'rotate(0)',
                        transition: 'transform 0.3s ease'
                      }}>
                        ▼
                      </div>
                    </div>

                    {selectedCategory === key && (
                      <div style={{
                        position: 'relative',
                        animation: 'fadeIn 0.3s ease'
                      }}>
                        {availableFiles.map((file, i) => (
                          <div
                            key={file.name}
                            onClick={(e) => {
                              e.stopPropagation();
                              downloadFile(file.name);
                            }}
                            style={{
                              padding: '1rem',
                              marginBottom: '0.5rem',
                              background: 'rgba(255, 255, 255, 0.05)',
                              borderRadius: '15px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease',
                              animation: `slideIn 0.3s ease ${i * 0.05}s backwards`
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = 'rgba(0, 212, 255, 0.1)';
                              e.currentTarget.style.transform = 'translateX(5px)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                              e.currentTarget.style.transform = 'translateX(0)';
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                              <span style={{ fontSize: '1.5rem' }}>{file.icon}</span>
                              <span style={{
                                fontSize: '1rem',
                                fontWeight: 600,
                                color: '#ffffff'
                              }}>
                                {file.label}
                              </span>
                            </div>
                            <div style={{
                              fontSize: '1.2rem',
                              color: category.color
                            }}>
                              ⬇
                            </div>
                          </div>
                        ))}

                        {availableFiles.length === 0 && (
                          <div style={{
                            textAlign: 'center',
                            padding: '2rem',
                            color: '#6b7280',
                            fontSize: '0.9rem'
                          }}>
                            No files available in this category
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {availableOutputs.length > 0 && (
            <div className="glass" style={{
              maxWidth: '1200px',
              margin: '4rem auto 2rem',
              padding: '3rem',
              borderRadius: '30px',
              textAlign: 'center',
              animation: 'fadeIn 1.2s ease'
            }}>
              <h4 style={{
                fontSize: '1.8rem',
                fontWeight: 800,
                color: '#00d4ff',
                marginBottom: '1.5rem'
              }}>
                🎉 ANALYSIS SUMMARY
              </h4>
              <div style={{
                fontSize: '1.2rem',
                color: '#b8c5d1',
                lineHeight: 1.8
              }}>
                Successfully generated <span style={{ 
                  color: '#00d4ff', 
                  fontWeight: 700,
                  fontSize: '1.5rem'
                }}>{availableOutputs.length}</span> comprehensive output files
                <br />
                from <span style={{ 
                  color: '#7b2cbf', 
                  fontWeight: 700,
                  fontSize: '1.5rem'
                }}>{analysisData && analysisData.total_comments ? analysisData.total_comments.toLocaleString() : '0'}</span> comments
              </div>
              <div style={{
                marginTop: '2rem',
                fontSize: '0.9rem',
                color: '#6b7280',
                fontStyle: 'italic'
              }}>
                All files include data exports, visualizations, temporal analysis,
                <br />
                linguistic metrics, engagement patterns, and comprehensive reports
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SENTICA;