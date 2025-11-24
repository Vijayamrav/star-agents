import React, { useState } from 'react'
import axios from 'axios'
import './ChatInterface.css'

interface Message {
    role: 'user' | 'assistant'
    content: string
}

interface ChatInterfaceProps {
    datasetId: number
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ datasetId }) => {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage: Message = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)

        try {
            // Use Text-to-SQL endpoint instead of general Q&A
            const response = await axios.post('/api/text-to-sql', {
                dataset_id: datasetId,
                question: input
            })

            let assistantContent = ''
            if (response.data.sql_query) {
                assistantContent = `Here is the SQL query for your request:\n\n\`\`\`sql\n${response.data.sql_query}\n\`\`\``
                if (response.data.needs_clarification) {
                    assistantContent += `\n\nNote: ${response.data.clarification_message}`
                }
            } else {
                assistantContent = response.data.clarification_message || "I couldn't generate a SQL query for that request."
            }

            const assistantMessage: Message = {
                role: 'assistant',
                content: assistantContent
            }
            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            const errorMessage: Message = {
                role: 'assistant',
                content: 'Sorry, I encountered an error generating the SQL query. Please try again.'
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <h3>🗄️ SQL Query Generator</h3>
                <p className="text-muted">Convert natural language to SQL</p>
            </div>

            <div className="chat-messages">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">⌨️</div>
                        <p className="text-secondary">Describe the data you want to retrieve, and I'll write the SQL!</p>
                        <div className="suggestion-chips">
                            <button
                                className="chip"
                                onClick={() => setInput('Show all employees in Sales department')}
                            >
                                Employees in Sales
                            </button>
                            <button
                                className="chip"
                                onClick={() => setInput('Count the number of rows')}
                            >
                                Count rows
                            </button>
                            <button
                                className="chip"
                                onClick={() => setInput('Select top 5 salaries')}
                            >
                                Top 5 salaries
                            </button>
                        </div>
                    </div>
                ) : (
                    messages.map((message, index) => (
                        <div
                            key={index}
                            className={`message ${message.role} animate-fade-in`}
                        >
                            <div className="message-avatar">
                                {message.role === 'user' ? '👤' : '🤖'}
                            </div>
                            <div className="message-content">
                                <div className="message-text">{message.content}</div>
                            </div>
                        </div>
                    ))
                )}

                {loading && (
                    <div className="message assistant animate-fade-in">
                        <div className="message-avatar">🤖</div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <form className="chat-input-form" onSubmit={handleSubmit}>
                <input
                    type="text"
                    className="input chat-input"
                    placeholder="e.g., Show me users older than 30..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={loading}
                />
                <button
                    type="submit"
                    className="btn btn-primary send-button"
                    disabled={!input.trim() || loading}
                >
                    {loading ? '⏳' : 'Generate SQL'}
                </button>
            </form>
        </div>
    )
}

export default ChatInterface
