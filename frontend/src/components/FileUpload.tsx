import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import './FileUpload.css'

interface FileUploadProps {
    onUploadSuccess?: (datasetId: number) => void
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
    const [file, setFile] = useState<File | null>(null)
    const [uploading, setUploading] = useState(false)
    const [analyzing, setAnalyzing] = useState(false)
    const [dragActive, setDragActive] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const navigate = useNavigate()

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true)
        } else if (e.type === 'dragleave') {
            setDragActive(false)
        }
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0])
        }
    }

    const handleFileSelect = (selectedFile: File) => {
        const validTypes = ['.csv', '.xlsx', '.xls']
        const fileExtension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase()

        if (!validTypes.includes(fileExtension)) {
            setError('Please upload a CSV or Excel file')
            return
        }

        setFile(selectedFile)
        setError(null)
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0])
        }
    }

    const handleUploadAndAnalyze = async () => {
        if (!file) return

        try {
            setUploading(true)
            setError(null)

            // Upload file
            const formData = new FormData()
            formData.append('file', file)

            const uploadResponse = await axios.post('/api/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })

            const datasetId = uploadResponse.data.dataset_id

            // Start analysis
            setUploading(false)
            setAnalyzing(true)

            const analysisResponse = await axios.post(`/api/analyze/${datasetId}`)
            const analysisId = analysisResponse.data.analysis_id

            // Navigate to dashboard
            navigate(`/dashboard/${analysisId}`)

            if (onUploadSuccess) {
                onUploadSuccess(datasetId)
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Upload failed. Please try again.')
            setUploading(false)
            setAnalyzing(false)
        }
    }

    return (
        <div className="file-upload-container">
            <div
                className={`upload-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <input
                    type="file"
                    id="file-input"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />

                {!file ? (
                    <label htmlFor="file-input" className="upload-label">
                        <div className="upload-icon">📊</div>
                        <h3>Drop your dataset here</h3>
                        <p className="text-muted">or click to browse</p>
                        <p className="text-muted" style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                            Supports CSV and Excel files
                        </p>
                    </label>
                ) : (
                    <div className="file-info animate-fade-in">
                        <div className="file-icon">📄</div>
                        <div className="file-details">
                            <h4>{file.name}</h4>
                            <p className="text-muted">{(file.size / 1024).toFixed(2)} KB</p>
                        </div>
                        <button
                            className="remove-file"
                            onClick={() => setFile(null)}
                            aria-label="Remove file"
                        >
                            ✕
                        </button>
                    </div>
                )}
            </div>

            {error && (
                <div className="error-message animate-fade-in">
                    ⚠️ {error}
                </div>
            )}

            {file && !uploading && !analyzing && (
                <button
                    className="btn btn-primary upload-button animate-fade-in"
                    onClick={handleUploadAndAnalyze}
                >
                    <span>🚀</span>
                    Upload & Analyze
                </button>
            )}

            {(uploading || analyzing) && (
                <div className="progress-container animate-fade-in">
                    <div className="spinner"></div>
                    <p className="text-secondary">
                        {uploading ? 'Uploading file...' : 'Running AI analysis...'}
                    </p>
                    <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                        This may take a moment
                    </p>
                </div>
            )}
        </div>
    )
}

export default FileUpload
