import React, { useState, useEffect } from 'react';
import { Card, Container, Row, Col, Badge, Spinner, Alert, Tabs, Tab, ListGroup } from 'react-bootstrap';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const NewsAnalysis = ({ symbol }) => {
  const [news, setNews] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('news');

  useEffect(() => {
    if (!symbol) return;
    
    setLoading(true);
    setError(null);
    
    // Fetch news articles
    axios.get(`${API_URL}/api/news/${symbol}`)
      .then(response => {
        setNews(response.data);
        
        // Fetch news analysis
        return axios.get(`${API_URL}/api/analysis/news/${symbol}`);
      })
      .then(response => {
        setAnalysis(response.data);
        
        // Fetch trading insights
        return axios.get(`${API_URL}/api/insights/${symbol}`);
      })
      .then(response => {
        setInsights(response.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching data:', err);
        setError('Failed to fetch data. Please try again later.');
        setLoading(false);
      });
  }, [symbol]);

  // Function to render sentiment badge
  const renderSentimentBadge = (sentiment) => {
    if (!sentiment) return null;
    
    let variant = 'secondary';
    
    switch (sentiment.toLowerCase()) {
      case 'bullish':
        variant = 'success';
        break;
      case 'bearish':
        variant = 'danger';
        break;
      case 'neutral':
        variant = 'warning';
        break;
      default:
        variant = 'secondary';
    }
    
    return <Badge bg={variant}>{sentiment}</Badge>;
  };

  // Function to render category badges
  const renderCategoryBadges = (categories) => {
    if (!categories || !Array.isArray(categories)) return null;
    
    return categories.map((category, index) => {
      let variant = 'info';
      
      switch (category.toLowerCase()) {
        case 'technology':
          variant = 'primary';
          break;
        case 'finance':
          variant = 'success';
          break;
        case 'healthcare':
          variant = 'danger';
          break;
        case 'energy':
          variant = 'warning';
          break;
        case 'consumer':
          variant = 'info';
          break;
        case 'manufacturing':
          variant = 'secondary';
          break;
        case 'defense':
          variant = 'dark';
          break;
        default:
          variant = 'light';
      }
      
      return (
        <Badge bg={variant} className="me-1" key={index}>
          {category}
        </Badge>
      );
    });
  };

  // Function to render recommendation badge
  const renderRecommendationBadge = (recommendation) => {
    if (!recommendation) return null;
    
    let variant = 'secondary';
    
    switch (recommendation.toLowerCase()) {
      case 'buy':
        variant = 'success';
        break;
      case 'sell':
        variant = 'danger';
        break;
      case 'hold':
        variant = 'warning';
        break;
      default:
        variant = 'secondary';
    }
    
    return <Badge bg={variant} className="fs-5">{recommendation.toUpperCase()}</Badge>;
  };

  if (loading) {
    return (
      <Container className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p className="mt-2">Loading news and analysis...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-4">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <h2>News & Analysis for {symbol}</h2>
      
      <Tabs
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k)}
        className="mb-3"
      >
        <Tab eventKey="news" title="News Articles">
          <Row>
            {news.map((article, index) => (
              <Col md={6} lg={4} key={index} className="mb-3">
                <Card className="h-100">
                  <Card.Body>
                    <Card.Title>{article.title}</Card.Title>
                    <Card.Subtitle className="mb-2 text-muted">
                      {new Date(article.published_at).toLocaleDateString()} - {article.source}
                    </Card.Subtitle>
                    <div className="mb-2">
                      {renderCategoryBadges(article.categories)}
                    </div>
                    <Card.Text>{article.description}</Card.Text>
                  </Card.Body>
                  <Card.Footer>
                    <Card.Link href={article.url} target="_blank" rel="noopener noreferrer">
                      Read Full Article
                    </Card.Link>
                  </Card.Footer>
                </Card>
              </Col>
            ))}
            
            {news.length === 0 && (
              <Col>
                <Alert variant="info">No news articles found for {symbol}.</Alert>
              </Col>
            )}
          </Row>
        </Tab>
        
        <Tab eventKey="analysis" title="News Analysis">
          {analysis ? (
            <Card>
              <Card.Header>
                <h4>
                  News Analysis {renderSentimentBadge(analysis.market_sentiment)}
                </h4>
              </Card.Header>
              <Card.Body>
                <h5>Summary</h5>
                <p>{analysis.summary}</p>
                
                <Row className="mt-4">
                  <Col md={4}>
                    <h5>Key Events</h5>
                    <ListGroup>
                      {analysis.key_events && analysis.key_events.map((event, index) => (
                        <ListGroup.Item key={index}>{event}</ListGroup.Item>
                      ))}
                      {(!analysis.key_events || analysis.key_events.length === 0) && (
                        <ListGroup.Item>No key events identified</ListGroup.Item>
                      )}
                    </ListGroup>
                  </Col>
                  
                  <Col md={4}>
                    <h5>Risks</h5>
                    <ListGroup>
                      {analysis.risks && analysis.risks.map((risk, index) => (
                        <ListGroup.Item key={index}>{risk}</ListGroup.Item>
                      ))}
                      {(!analysis.risks || analysis.risks.length === 0) && (
                        <ListGroup.Item>No risks identified</ListGroup.Item>
                      )}
                    </ListGroup>
                  </Col>
                  
                  <Col md={4}>
                    <h5>Opportunities</h5>
                    <ListGroup>
                      {analysis.opportunities && analysis.opportunities.map((opportunity, index) => (
                        <ListGroup.Item key={index}>{opportunity}</ListGroup.Item>
                      ))}
                      {(!analysis.opportunities || analysis.opportunities.length === 0) && (
                        <ListGroup.Item>No opportunities identified</ListGroup.Item>
                      )}
                    </ListGroup>
                  </Col>
                </Row>
                
                <h5 className="mt-4">Detailed Analysis</h5>
                <p>{analysis.analysis}</p>
              </Card.Body>
            </Card>
          ) : (
            <Alert variant="info">No analysis available for {symbol}.</Alert>
          )}
        </Tab>
        
        <Tab eventKey="insights" title="Trading Insights">
          {insights ? (
            <Card>
              <Card.Header>
                <h4>
                  Trading Recommendation: {renderRecommendationBadge(insights.recommendation)}
                </h4>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <Card className="mb-3">
                      <Card.Header>
                        <h5>Trading Parameters</h5>
                      </Card.Header>
                      <ListGroup variant="flush">
                        <ListGroup.Item>
                          <strong>Confidence:</strong> {insights.confidence ? `${(insights.confidence * 100).toFixed(0)}%` : 'N/A'}
                        </ListGroup.Item>
                        <ListGroup.Item>
                          <strong>Time Horizon:</strong> {insights.time_horizon || 'N/A'}
                        </ListGroup.Item>
                        <ListGroup.Item>
                          <strong>Risk/Reward Ratio:</strong> {insights.risk_reward_ratio || 'N/A'}
                        </ListGroup.Item>
                      </ListGroup>
                    </Card>
                    
                    <Card>
                      <Card.Header>
                        <h5>Price Levels</h5>
                      </Card.Header>
                      <ListGroup variant="flush">
                        <ListGroup.Item>
                          <strong>Entry Points:</strong>{' '}
                          {insights.entry_points && insights.entry_points.length > 0
                            ? insights.entry_points.join(', ')
                            : 'N/A'}
                        </ListGroup.Item>
                        <ListGroup.Item>
                          <strong>Exit Points:</strong>{' '}
                          {insights.exit_points && insights.exit_points.length > 0
                            ? insights.exit_points.join(', ')
                            : 'N/A'}
                        </ListGroup.Item>
                        <ListGroup.Item>
                          <strong>Stop Loss:</strong> {insights.stop_loss || 'N/A'}
                        </ListGroup.Item>
                        <ListGroup.Item>
                          <strong>Take Profit:</strong> {insights.take_profit || 'N/A'}
                        </ListGroup.Item>
                      </ListGroup>
                    </Card>
                  </Col>
                  
                  <Col md={6}>
                    <Card>
                      <Card.Header>
                        <h5>Rationale</h5>
                      </Card.Header>
                      <Card.Body>
                        <p>{insights.rationale}</p>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          ) : (
            <Alert variant="info">No trading insights available for {symbol}.</Alert>
          )}
        </Tab>
      </Tabs>
    </Container>
  );
};

export default NewsAnalysis;