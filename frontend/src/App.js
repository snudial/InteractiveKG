import React, { useState } from 'react';
import GraphVisualization from './components/GraphVisualization';
import QuestionInput from './components/QuestionInput';
import './App.css';

function App() {
  const [graphData, setGraphData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQuestionSubmit = async (question) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log('Sending request to backend...'); // Debug log
      const response = await fetch('http://127.0.0.1:5001/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ question }),
        mode: 'cors',
      });

      console.log('Response received:', response.status); // Debug log

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Server error');
      }

      const data = await response.json();
      console.log('Data received:', data); // Debug log
      setGraphData(data);
    } catch (err) {
      console.error('Error details:', err); // Debug log
      setError(err.message || 'Failed to get response from server');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Graph of Thought Visualization</h1>
      <QuestionInput onSubmit={handleQuestionSubmit} isLoading={isLoading} />
      {error && (
        <div className="error-message">
          Error: {error}
          <br />
          <small>Please check if the backend server is running on port 5001</small>
        </div>
      )}
      {graphData && <GraphVisualization data={graphData} />}
      {!graphData && !isLoading && (
        <div className="placeholder">
          Enter a question to generate the graph visualization
        </div>
      )}
    </div>
  );
}

export default App;
