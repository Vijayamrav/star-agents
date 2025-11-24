import React from 'react'
import FileUpload from '../components/FileUpload'
import './Home.css'

const Home: React.FC = () => {
    return (
        <div className="home-page">
            <div className="hero-section">
                <div className="container">
                    <div className="hero-content animate-fade-in">
                        <h1 className="hero-title">
                            AI Data Analyst
                            <span className="gradient-text"> Agent Platform</span>
                        </h1>
                        <p className="hero-subtitle">
                            Upload your dataset and let AI agents automatically clean, analyze, and generate insights
                        </p>

                        <div className="features-grid">
                            <div className="feature-card card-glass">
                                <div className="feature-icon">🧹</div>
                                <h3>Data Cleaning</h3>
                                <p className="text-muted">Automatically handle missing values and duplicates</p>
                            </div>

                            <div className="feature-card card-glass">
                                <div className="feature-icon">📊</div>
                                <h3>Statistics</h3>
                                <p className="text-muted">Generate comprehensive summary statistics</p>
                            </div>

                            <div className="feature-card card-glass">
                                <div className="feature-icon">🔍</div>
                                <h3>Anomaly Detection</h3>
                                <p className="text-muted">Identify outliers and unusual patterns</p>
                            </div>

                            <div className="feature-card card-glass">
                                <div className="feature-icon">📈</div>
                                <h3>Visualizations</h3>
                                <p className="text-muted">Create beautiful charts automatically</p>
                            </div>

                            <div className="feature-card card-glass">
                                <div className="feature-icon">💡</div>
                                <h3>AI Insights</h3>
                                <p className="text-muted">Get intelligent recommendations</p>
                            </div>

                            <div className="feature-card card-glass">
                                <div className="feature-icon">🗄️</div>
                                <h3>SQL Generation</h3>
                                <p className="text-muted">Generate SQL queries for your data</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="upload-section">
                <div className="container">
                    <div className="upload-wrapper animate-slide-in">
                        <h2 className="section-heading">Get Started</h2>
                        <p className="section-subheading text-secondary">
                            Upload your CSV or Excel file to begin the analysis
                        </p>
                        <FileUpload />
                    </div>
                </div>
            </div>

            <footer className="footer">
                <div className="container">
                    <p className="text-muted">
                        Powered by LangGraph, FastAPI, React, and DeepSeek AI
                    </p>
                </div>
            </footer>
        </div>
    )
}

export default Home
