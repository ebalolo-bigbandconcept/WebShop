import React from 'react';

/**
 * ErrorBoundary component to catch and display errors gracefully
 * instead of showing a white screen when an error occurs
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.error('Error caught by boundary:', error);
    console.error('Error info:', errorInfo);

    // Update state with error details
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Optional: You could also log to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="alert alert-danger m-4" role="alert">
          <h4 className="alert-heading">Une erreur s'est produite</h4>
          <p>
            Désolé, quelque chose s'est mal passé. L'application a rencontré une erreur inattendue.
          </p>
          {process.env.NODE_ENV === 'development' && (
            <details style={{ whiteSpace: 'pre-wrap', marginTop: '1rem' }}>
              <summary>Détails de l'erreur (développement seulement)</summary>
              {this.state.error && this.state.error.toString()}
              {this.state.errorInfo && this.state.errorInfo.componentStack}
            </details>
          )}
          <div className="mt-3">
            <button
              className="btn btn-primary me-2"
              onClick={this.handleReset}
            >
              Réessayer
            </button>
            <a href="/" className="btn btn-secondary">
              Retour à l'accueil
            </a>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
