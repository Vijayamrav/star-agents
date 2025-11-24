import React, { useState } from 'react'
import axios from 'axios'
import './TextToSQL.css'

interface TextToSQLProps {
    datasetId: number
}

const TextToSQL: React.FC<TextToSQLProps> = ({ datasetId }) => {
    const [question, setQuestion] = useState('')
    const [sqlQuery, setSqlQuery] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [clarification, setClarification] = useState<string | null>(null)
    const [copied, setCopied] = useState(false)

    const exampleQuestions = [
        "Show all records",
        "What is the average salary?",
        "Count records by department",
        "Top 5 highest values",
        "Show records where salary > 60000"
    ]

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!question.trim()) return

        setLoading(true)
        setError(null)
        setClarification(null)
        setSqlQuery(null)
        setCopied(false)

        try {
            const response = await axios.post('/api/text-to-sql', {
                dataset_id: datasetId,
                question: question
            })

            if (response.data.needs_clarification) {
                setClarification(response.data.clarification_message)
            } else {
                setSqlQuery(response.data.sql_query)
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to generate SQL query')
        } finally {
            setLoading(false)
        }
    }

    const handleCopy = () => {
        if (sqlQuery) {
            navigator.clipboard.writeText(sqlQuery)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    const handleExampleClick = (example: string) => {
        setQuestion(example)
    }

    return (
        <div className="text-to-sql-container">
            <div className="text-to-sql-header">
                <h2>
                    <span className="sql-icon">🔍</span>
                    Text-to-SQL Query Generator
                </h2>
                <p className="sql-description">
                    Ask questions in natural language and get valid PostgreSQL queries
                </p>
            </div>

            <form onSubmit={handleSubmit} className="sql-form">
                <div className="input-group">
                    <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Ask a question about your data..."
                        className="sql-input"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        className="sql-submit-btn"
                        disabled={loading || !question.trim()}
                    >
                        {loading ? (
                            <>
                                <span className="spinner-small"></span>
                                Generating...
                            </>
                        ) : (
                            <>
                                <span>⚡</span>
                                Generate SQL
                            </>
                        )}
                    </button>
                </div>
            </form>

            {/* Example Questions */}
            <div className="example-questions">
                <span className="example-label">Try these:</span>
                <div className="example-chips">
                    {exampleQuestions.map((example, index) => (
                        <button
                            key={index}
                            className="example-chip"
                            onClick={() => handleExampleClick(example)}
                            disabled={loading}
                        >
                            {example}
                        </button>
                    ))}
                </div>
            </div>

            {/* SQL Output */}
            {sqlQuery && (
                <div className="sql-output card-glass animate-fade-in">
                    <div className="output-header">
                        <h3>Generated SQL Query</h3>
                        <button
                            className={`copy-btn ${copied ? 'copied' : ''}`}
                            onClick={handleCopy}
                        >
                            {copied ? (
                                <>
                                    <span>✓</span>
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <span>📋</span>
                                    Copy
                                </>
                            )}
                        </button>
                    </div>
                    <pre className="sql-code-block">{sqlQuery}</pre>
                </div>
            )}

            {/* Clarification Message */}
            {clarification && (
                <div className="clarification-message card-glass animate-fade-in">
                    <div className="clarification-icon">💭</div>
                    <div className="clarification-content">
                        <h4>Clarification Needed</h4>
                        <p>{clarification}</p>
                    </div>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="error-message animate-fade-in">
                    <span className="error-icon">⚠️</span>
                    {error}
                </div>
            )}
        </div>
    )
}

export default TextToSQL
