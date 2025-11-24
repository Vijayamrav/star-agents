import React, { useEffect, useState } from 'react'
import axios from 'axios'
import './AnalysisDashboard.css'

interface AnalysisData {
    id: number
    dataset_id: number
    status: string
    cleaning_report: any
    statistics: any
    anomalies: any
    insights: string
    sql_queries: string
    visualizations: Array<{
        id: number
        type: string
        url: string
    }>
    error_message?: string
}

interface AnalysisDashboardProps {
    analysisId: number
}

const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({ analysisId }) => {
    const [analysis, setAnalysis] = useState<AnalysisData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedVizIndex, setSelectedVizIndex] = useState(0)

    useEffect(() => {
        fetchAnalysis()
        const interval = setInterval(() => {
            if (analysis?.status === 'processing') {
                fetchAnalysis()
            }
        }, 3000)

        return () => clearInterval(interval)
    }, [analysisId])

    const fetchAnalysis = async () => {
        try {
            const response = await axios.get(`/api/analysis/${analysisId}`)
            setAnalysis(response.data)
            setLoading(false)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load analysis')
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="dashboard-loading">
                <div className="spinner"></div>
                <p className="text-secondary">Loading analysis results...</p>
            </div>
        )
    }

    if (error || !analysis) {
        return (
            <div className="dashboard-error">
                <div className="error-icon">⚠️</div>
                <h3>Failed to Load Analysis</h3>
                <p className="text-muted">{error}</p>
            </div>
        )
    }

    if (analysis.status === 'processing') {
        return (
            <div className="dashboard-processing">
                <div className="spinner"></div>
                <h3>AI Analysis in Progress</h3>
                <p className="text-secondary">Your data is being analyzed...</p>
                <div className="processing-steps">
                    <div className="step completed">✓ Data Cleaning</div>
                    <div className="step active">⏳ Generating Statistics</div>
                    <div className="step">Detecting Anomalies</div>
                    <div className="step">Creating Visualizations</div>
                    <div className="step">Generating Insights</div>
                </div>
            </div>
        )
    }

    if (analysis.status === 'failed') {
        return (
            <div className="dashboard-error">
                <div className="error-icon">❌</div>
                <h3>Analysis Failed</h3>
                <p className="text-muted">{analysis.error_message}</p>
            </div>
        )
    }

    const stats = analysis.statistics || {}
    const anomalies = analysis.anomalies || {}
    const cleaning = analysis.cleaning_report || {}

    return (
        <div className="analysis-dashboard animate-fade-in">
            {/* Status Banner */}
            <div className="status-banner success">
                <span className="status-icon">✅</span>
                <span>Analysis completed successfully!</span>
            </div>

            {/* Summary Cards */}
            <div className="summary-grid">
                <div className="summary-card card-glass">
                    <div className="card-icon">📊</div>
                    <div className="card-content">
                        <h4>Dataset Size</h4>
                        <p className="card-value">{stats.shape?.[0] || 0} rows</p>
                        <p className="text-muted">{stats.shape?.[1] || 0} columns</p>
                    </div>
                </div>

                <div className="summary-card card-glass">
                    <div className="card-icon">🧹</div>
                    <div className="card-content">
                        <h4>Data Cleaned</h4>
                        <p className="card-value">{cleaning.rows_removed || 0} rows removed</p>
                        <p className="text-muted">{cleaning.duplicates || 0} duplicates</p>
                        {cleaning.cleaned_file_path && (
                            <button
                                className="download-btn"
                                onClick={() => window.open(`http://localhost:8000/api/download/${analysis.dataset_id}/cleaned`, '_blank')}
                                title="Download Cleaned Dataset"
                            >
                                📥 Download CSV
                            </button>
                        )}
                    </div>
                </div>

                <div className="summary-card card-glass">
                    <div className="card-icon">⚠️</div>
                    <div className="card-content">
                        <h4>Anomalies</h4>
                        <p className="card-value">
                            {Object.keys(anomalies.outliers || {}).length} columns
                        </p>
                        <p className="text-muted">with outliers</p>
                    </div>
                </div>

                <div className="summary-card card-glass">
                    <div className="card-icon">📈</div>
                    <div className="card-content">
                        <h4>Visualizations</h4>
                        <p className="card-value">{analysis.visualizations?.length || 0}</p>
                        <p className="text-muted">charts generated</p>
                    </div>
                </div>
            </div>

            {/* Insights Section */}
            {analysis.insights && (
                <div className="section">
                    <h2 className="section-title">
                        <span className="section-icon">💡</span>
                        AI-Generated Insights
                    </h2>
                    <div className="insights-card card-glass">
                        <div className="insights-content">{analysis.insights}</div>
                    </div>
                </div>
            )}

            {/* Visualizations Section with Dropdown */}
            {analysis.visualizations && analysis.visualizations.length > 0 && (
                <div className="section">
                    <div className="viz-header">
                        <h2 className="section-title">
                            <span className="section-icon">�</span>
                            Visualizations
                        </h2>
                        <div className="viz-selector">
                            <label htmlFor="viz-select" className="viz-label">Select Chart:</label>
                            <select
                                id="viz-select"
                                className="viz-dropdown"
                                value={selectedVizIndex}
                                onChange={(e) => setSelectedVizIndex(Number(e.target.value))}
                            >
                                {analysis.visualizations.map((viz, index) => (
                                    <option key={viz.id} value={index}>
                                        {viz.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="viz-display card">
                        <div className="viz-type-badge">
                            {analysis.visualizations[selectedVizIndex].type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <img
                            src={analysis.visualizations[selectedVizIndex].url}
                            alt={analysis.visualizations[selectedVizIndex].type}
                            className="viz-image-single"
                            loading="lazy"
                        />
                    </div>
                </div>
            )}

            {/* Anomalies Section */}
            {(Object.keys(anomalies.outliers || {}).length > 0 ||
                Object.keys(anomalies.domain_anomalies || {}).length > 0 ||
                Object.keys(anomalies.invalid_values || {}).length > 0) && (
                    <div className="section">
                        <h2 className="section-title">
                            <span className="section-icon">🔍</span>
                            Detected Anomalies
                        </h2>
                        <div className="anomalies-grid">
                            {/* Statistical Outliers */}
                            {Object.entries(anomalies.outliers || {}).map(([column, data]: [string, any]) => (
                                <div key={`outlier-${column}`} className="anomaly-card card-glass">
                                    <h4>{column} (Outliers)</h4>
                                    <div className="anomaly-stats">
                                        <div className="stat">
                                            <span className="stat-label">Count:</span>
                                            <span className="stat-value">{data.count}</span>
                                        </div>
                                        <div className="stat">
                                            <span className="stat-label">Percentage:</span>
                                            <span className="stat-value">{data.percentage}%</span>
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {/* Domain Anomalies */}
                            {Object.entries(anomalies.domain_anomalies || {}).map(([rule, indices]: [string, any]) => (
                                <div key={`domain-${rule}`} className="anomaly-card card-glass">
                                    <h4>Domain Rule Violation</h4>
                                    <div className="anomaly-stats">
                                        <div className="stat">
                                            <span className="stat-label">Rule:</span>
                                            <span className="stat-value" style={{ fontSize: '0.9em' }}>{rule.replace(/_/g, ' ')}</span>
                                        </div>
                                        <div className="stat">
                                            <span className="stat-label">Affected Rows:</span>
                                            <span className="stat-value">{Array.isArray(indices) ? indices.length : 0}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {/* Invalid Values */}
                            {Object.entries(anomalies.invalid_values || {}).map(([column, values]: [string, any]) => (
                                <div key={`invalid-${column}`} className="anomaly-card card-glass">
                                    <h4>Invalid Values: {column}</h4>
                                    <div className="anomaly-stats">
                                        <div className="stat">
                                            <span className="stat-label">Count:</span>
                                            <span className="stat-value">{Array.isArray(values) ? values.length : 0}</span>
                                        </div>
                                        <div className="stat">
                                            <span className="stat-label">Examples:</span>
                                            <span className="stat-value" style={{ fontSize: '0.8em', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                {Array.isArray(values) ? values.slice(0, 3).join(', ') : ''}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

            {/* SQL Queries Section */}
            {analysis.sql_queries && (
                <div className="section">
                    <h2 className="section-title">
                        <span className="section-icon">🗄️</span>
                        SQL Schema & Queries
                    </h2>
                    <div className="sql-card card">
                        <pre className="sql-code">{analysis.sql_queries}</pre>
                    </div>
                </div>
            )}

            {/* Statistics Section */}
            {stats.numeric_summary && (
                <div className="section">
                    <h2 className="section-title">
                        <span className="section-icon">📈</span>
                        Statistical Summary
                    </h2>
                    <div className="stats-table-container card">
                        <div className="stats-scroll">
                            <table className="stats-table">
                                <thead>
                                    <tr>
                                        <th>Statistic</th>
                                        {Object.keys(stats.numeric_summary).map((col) => (
                                            <th key={col}>{col}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max'].map((stat) => (
                                        <tr key={stat}>
                                            <td className="stat-name">{stat}</td>
                                            {Object.values(stats.numeric_summary).map((colData: any, idx) => (
                                                <td key={idx}>
                                                    {typeof colData[stat] === 'number'
                                                        ? colData[stat].toFixed(2)
                                                        : colData[stat]}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default AnalysisDashboard
