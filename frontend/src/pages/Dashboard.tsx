import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import AnalysisDashboard from '../components/AnalysisDashboard'
import ChatInterface from '../components/ChatInterface'
import './Dashboard.css'

const Dashboard: React.FC = () => {
    const { analysisId } = useParams<{ analysisId: string }>()
    const [datasetId, setDatasetId] = useState<number | null>(null)

    useEffect(() => {
        if (analysisId) {
            fetchDatasetId()
        }
    }, [analysisId])

    const fetchDatasetId = async () => {
        try {
            const response = await axios.get(`/api/analysis/${analysisId}`)
            setDatasetId(response.data.dataset_id)
        } catch (error) {
            console.error('Failed to fetch dataset ID:', error)
        }
    }

    return (
        <div className="dashboard-page">
            <header className="dashboard-header">
                <div className="container">
                    <div className="header-content">
                        <Link to="/" className="logo">
                            <span className="logo-icon">🤖</span>
                            <span className="logo-text">
                                AI Data Analyst <span className="gradient-text">Agent</span>
                            </span>
                        </Link>
                        <Link to="/" className="btn btn-secondary">
                            ← New Analysis
                        </Link>
                    </div>
                </div>
            </header>

            <main className="dashboard-main">
                <div className="container">
                    <div className="dashboard-grid">
                        <div className="dashboard-content">
                            {analysisId && (
                                <AnalysisDashboard analysisId={parseInt(analysisId)} />
                            )}
                        </div>

                        <aside className="dashboard-sidebar">
                            {datasetId && (
                                <>
                                    <ChatInterface datasetId={datasetId} />
                                </>
                            )}
                        </aside>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default Dashboard
