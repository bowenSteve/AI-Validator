import { useEffect, useState } from "react";
import { History as HistoryIcon, CheckSquare, AlertTriangle, Clock, Eye, Calendar, FileText, Image, Trash2 } from 'lucide-react';
import SessionDetailsModal from './components/SessionDetailsModal';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function History({ isDark }) {
    const [comparisonSessions, setComparisonSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedSession, setSelectedSession] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                setLoading(true);
                
                // Fetch both uploads and validations in parallel
                const [uploadsResponse, validationsResponse] = await Promise.all([
                    fetch(`${API_URL}/api/history/uploads?limit=100`),
                    fetch(`${API_URL}/api/history/validations?limit=100`)
                ]);

                if (!uploadsResponse.ok || !validationsResponse.ok) {
                    throw new Error('Failed to fetch history data');
                }
                
                const uploadsData = await uploadsResponse.json();
                const validationsData = await validationsResponse.json();
                
                const allUploads = uploadsData.uploads || [];
                const allValidations = validationsData.validations || [];
                
                // Group uploads by their validation sessions
                const sessions = createComparisonSessions(allUploads, allValidations);
                setComparisonSessions(sessions);
                
            } catch (error) {
                console.error('Failed to fetch history:', error);
                setError('Failed to load history. Please try again later.');
            } finally {
                setLoading(false);
            }
        };
        
        fetchHistory();
    }, []);

    const createComparisonSessions = (uploads, validations) => {
        const sessions = [];
        const usedUploadIds = new Set();
        
        // Create sessions from validations (comparisons)
        validations.forEach(validation => {
            // Handle both old single-image format and new multi-image format
            let mainUploads = [];
            let secondaryUploads = [];
            
            if (validation.main_upload_id && validation.secondary_upload_id) {
                // Old format: single main_upload_id and secondary_upload_id
                const mainUpload = uploads.find(u => u.upload_id === validation.main_upload_id);
                const secondaryUpload = uploads.find(u => u.upload_id === validation.secondary_upload_id);
                if (mainUpload) mainUploads.push(mainUpload);
                if (secondaryUpload) secondaryUploads.push(secondaryUpload);
            } else if (validation.comparison_type === 'gemini_validation_multi') {
                // New format: find uploads by matching timestamps and types
                // Get uploads from around the validation time (within 5 minutes)
                const validationTime = new Date(validation.comparison_date);
                const timeWindow = 5 * 60 * 1000; // 5 minutes in milliseconds
                
                mainUploads = uploads.filter(u => {
                    const uploadTime = new Date(u.upload_date);
                    return u.image_type === 'main' && 
                           Math.abs(uploadTime - validationTime) <= timeWindow;
                });
                
                secondaryUploads = uploads.filter(u => {
                    const uploadTime = new Date(u.upload_date);
                    return u.image_type === 'secondary' && 
                           Math.abs(uploadTime - validationTime) <= timeWindow;
                });
            }
            
            // Only create session if we have at least one main and one secondary upload
            if (mainUploads.length > 0 && secondaryUploads.length > 0) {
                sessions.push({
                    id: validation.comparison_id,
                    type: 'comparison',
                    date: validation.comparison_date,
                    mainUpload: mainUploads[0], // Use first main upload for display
                    secondaryUpload: secondaryUploads[0], // Use first secondary upload for display
                    mainUploads: mainUploads, // Store all main uploads
                    secondaryUploads: secondaryUploads, // Store all secondary uploads
                    validation,
                    accuracy: validation.accuracy_score || 0
                });
                
                // Mark all used uploads
                mainUploads.forEach(u => usedUploadIds.add(u.upload_id));
                secondaryUploads.forEach(u => usedUploadIds.add(u.upload_id));
            }
        });
        
        // Add standalone uploads (not part of any comparison)
        uploads.forEach(upload => {
            if (!usedUploadIds.has(upload.upload_id)) {
                sessions.push({
                    id: upload.upload_id,
                    type: 'standalone',
                    date: upload.upload_date,
                    upload,
                    validation: null,
                    accuracy: null
                });
            }
        });
        
        // Sort by date (newest first)
        return sessions.sort((a, b) => new Date(b.date) - new Date(a.date));
    };
    
    const getStatusIcon = (similarity) => {
        if (similarity >= 90) {
            return <CheckSquare className="text-green-500" size={16} />;
        } else if (similarity >= 70) {
            return <Clock className="text-yellow-500" size={16} />;
        } else {
            return <AlertTriangle className="text-red-500" size={16} />;
        }
    };

    const getStatusColor = (similarity) => {
        if (similarity >= 90) {
            return isDark ? 'text-green-400' : 'text-green-600';
        } else if (similarity >= 70) {
            return isDark ? 'text-yellow-400' : 'text-yellow-600';
        } else {
            return isDark ? 'text-red-400' : 'text-red-600';
        }
    };

    const getStatusBadge = (similarity) => {
        if (similarity >= 90) {
            return isDark 
                ? 'bg-green-900/20 text-green-400 border-green-800' 
                : 'bg-green-100 text-green-700 border-green-200';
        } else if (similarity >= 70) {
            return isDark 
                ? 'bg-yellow-900/20 text-yellow-400 border-yellow-800' 
                : 'bg-yellow-100 text-yellow-700 border-yellow-200';
        } else {
            return isDark 
                ? 'bg-red-900/20 text-red-400 border-red-800' 
                : 'bg-red-100 text-red-700 border-red-200';
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return {
            date: date.toLocaleDateString(),
            time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
    };
    
    const handleViewSession = (session) => {
        setSelectedSession(session);
        setIsModalOpen(true);
    };
    
    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedSession(null);
    };
    
    const handleDeleteSession = async (session) => {
        if (!window.confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
            return;
        }
        
        try {
            if (session.type === 'comparison') {
                // Delete comparison and associated uploads
                const deletePromises = [
                    fetch(`${API_URL}/api/validation/result/${session.validation.comparison_id}`, { method: 'DELETE' })
                ];
                
                // Delete all main uploads
                if (session.mainUploads && session.mainUploads.length > 0) {
                    session.mainUploads.forEach(upload => {
                        deletePromises.push(
                            fetch(`${API_URL}/api/history/uploads/${upload.upload_id}`, { method: 'DELETE' })
                        );
                    });
                } else if (session.mainUpload) {
                    // Fallback for old format
                    deletePromises.push(
                        fetch(`${API_URL}/api/history/uploads/${session.mainUpload.upload_id}`, { method: 'DELETE' })
                    );
                }
                
                // Delete all secondary uploads
                if (session.secondaryUploads && session.secondaryUploads.length > 0) {
                    session.secondaryUploads.forEach(upload => {
                        deletePromises.push(
                            fetch(`${API_URL}/api/history/uploads/${upload.upload_id}`, { method: 'DELETE' })
                        );
                    });
                } else if (session.secondaryUpload) {
                    // Fallback for old format
                    deletePromises.push(
                        fetch(`${API_URL}/api/history/uploads/${session.secondaryUpload.upload_id}`, { method: 'DELETE' })
                    );
                }
                
                const responses = await Promise.all(deletePromises);
                
                // Check if all deletes were successful
                const failedDeletes = responses.filter(response => !response.ok);
                if (failedDeletes.length > 0) {
                    throw new Error(`Failed to delete ${failedDeletes.length} items`);
                }
            } else {
                // Delete standalone upload
                const response = await fetch(`${API_URL}/api/history/uploads/${session.upload.upload_id}`, { method: 'DELETE' });
                if (!response.ok) {
                    throw new Error('Failed to delete upload');
                }
            }
            
            // Remove session from state
            setComparisonSessions(prev => prev.filter(s => s.id !== session.id));
            
        } catch (error) {
            console.error('Failed to delete session:', error);
            alert('Failed to delete session. Please try again.');
        }
    };
    
    const getSessionName = (session) => {
        const timestamp = new Date(session.date).getTime();
        return session.type === 'comparison' 
            ? `validation_session_${timestamp}`
            : `standalone_upload_${timestamp}`;
    };

    if (loading) {
        return (
            <div className="h-full p-6">
                <div className="flex items-center space-x-2 mb-6">
                    <HistoryIcon size={24} className={isDark ? 'text-cyan-400' : 'text-blue-500'} />
                    <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        History
                    </h1>
                </div>
                
                <div className="flex items-center justify-center h-64">
                    <div className={`animate-spin rounded-full h-12 w-12 border-b-2 ${
                        isDark ? 'border-cyan-400' : 'border-blue-500'
                    }`}></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full p-6">
                <div className="flex items-center space-x-2 mb-6">
                    <HistoryIcon size={24} className={isDark ? 'text-cyan-400' : 'text-blue-500'} />
                    <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        History
                    </h1>
                </div>
                
                <div className={`p-4 rounded-lg border ${
                    isDark 
                        ? 'bg-red-900/20 border-red-800 text-red-300' 
                        : 'bg-red-50 border-red-200 text-red-700'
                }`}>
                    <div className="flex items-center space-x-2">
                        <AlertTriangle size={16} />
                        <span>{error}</span>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                    <HistoryIcon size={24} className={isDark ? 'text-cyan-400' : 'text-blue-500'} />
                    <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        History
                    </h1>
                </div>
                <div className="flex items-center space-x-4 pr-5">
                    <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        {comparisonSessions.filter(s => s.type === 'comparison').length} comparisons • {comparisonSessions.filter(s => s.type === 'standalone').length} standalone uploads
                    </span>
                </div>
            </div>

            {/* Sessions Header */}
            <div className="mb-6">
                <div className="flex items-center space-x-2">
                    <Eye size={20} className={isDark ? 'text-cyan-400' : 'text-blue-500'} />
                    <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        Validation Sessions ({comparisonSessions.length})
                    </h2>
                </div>
                <p className={`mt-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Review your image comparisons and validation results
                </p>
            </div>

            {/* Sessions Content */}
            {comparisonSessions.length === 0 ? (
                <div className={`flex flex-col items-center justify-center h-64 rounded-lg border-2 border-dashed ${
                    isDark ? 'border-gray-700' : 'border-gray-200'
                }`}>
                    <Eye size={48} className={isDark ? 'text-gray-600' : 'text-gray-400'} />
                    <h3 className={`mt-4 text-lg font-medium ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        No sessions found
                    </h3>
                    <p className={`mt-1 text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        Your comparison sessions will appear here
                    </p>
                </div>
            ) : (
                <div className="space-y-6">
                    {comparisonSessions.map((session) => {
                            const { date, time } = formatDate(session.date);
                            
                            return (
                                <div key={session.id} className={`p-6 rounded-lg border transition-colors duration-150 hover:shadow-md ${
                                    isDark 
                                        ? 'bg-gray-800 border-gray-700 hover:bg-gray-750' 
                                        : 'bg-white border-gray-200 hover:bg-gray-50'
                                }`}>
                                    {session.type === 'comparison' ? (
                                        /* Comparison Session */
                                        <div>
                                            <div className="flex items-center justify-between mb-4">
                                                <div className="flex items-center space-x-3">
                                                    {getStatusIcon(session.accuracy)}
                                                    <div>
                                                        <h3 className={`text-lg font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                            {getSessionName(session)}
                                                        </h3>
                                                        <div className="flex items-center space-x-4 mt-1">
                                                            <div className="flex items-center space-x-1">
                                                                <Calendar size={14} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                                <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                    {date} at {time}
                                                                </span>
                                                            </div>
                                                            <span className={`px-2 py-1 text-xs font-medium rounded border ${getStatusBadge(session.accuracy)}`}>
                                                                {session.accuracy >= 90 ? 'Excellent' : session.accuracy >= 70 ? 'Good' : 'Needs Review'} ({session.accuracy.toFixed(0)}%)
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center space-x-2">
                                                    <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                                        {session.validation?.comparison_type === 'gemini_validation' ? 'Gemini AI' : 'Text Comparison'}
                                                    </span>
                                                    <button
                                                        onClick={() => handleViewSession(session)}
                                                        className={`p-2 rounded-lg transition-colors duration-150 ${
                                                            isDark 
                                                                ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                                                                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                                                        }`}
                                                        title="View session details"
                                                    >
                                                        <Eye size={16} />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteSession(session)}
                                                        className={`p-2 rounded-lg transition-colors duration-150 ${
                                                            isDark 
                                                                ? 'text-red-400 hover:text-red-300 hover:bg-red-900/20' 
                                                                : 'text-red-500 hover:text-red-700 hover:bg-red-50'
                                                        }`}
                                                        title="Delete session"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                            
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                {/* Main Upload */}
                                                <div className={`p-4 rounded-lg border ${
                                                    isDark ? 'border-blue-600 bg-blue-900/10' : 'border-blue-200 bg-blue-50'
                                                }`}>
                                                    <div className="flex items-center space-x-2 mb-3">
                                                        <div className={`w-3 h-3 rounded-full ${
                                                            isDark ? 'bg-blue-400' : 'bg-blue-500'
                                                        }`}></div>
                                                        <span className={`text-sm font-medium ${
                                                            isDark ? 'text-blue-300' : 'text-blue-700'
                                                        }`}>
                                                            Util Screenshot{session.mainUploads && session.mainUploads.length > 1 ? ` (${session.mainUploads.length})` : ''}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-start space-x-3">
                                                        <div className={`w-16 h-16 rounded-lg flex items-center justify-center ${
                                                            isDark ? 'bg-gray-700' : 'bg-gray-100'
                                                        }`}>
                                                            <Image className={isDark ? 'text-gray-500' : 'text-gray-400'} size={20} />
                                                        </div>
                                                        <div className="flex-1">
                                                            <h4 className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                                {session.mainUpload.original_filename}
                                                            </h4>
                                                            <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                {(session.mainUpload.file_size / 1024 / 1024).toFixed(2)} MB
                                                            </p>
                                                        </div>
                                                    </div>
                                                    {session.mainUpload.extracted_text && (
                                                        <div className={`mt-3 p-3 rounded border ${
                                                            isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                                                        }`}>
                                                            <div className="flex items-center justify-between mb-2">
                                                                <span className={`text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                                    Extracted Text
                                                                </span>
                                                                <FileText size={12} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                            </div>
                                                            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                                                {session.mainUpload.extracted_text.length > 120 
                                                                    ? `${session.mainUpload.extracted_text.substring(0, 120)}...`
                                                                    : session.mainUpload.extracted_text
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                                
                                                {/* Secondary Upload */}
                                                <div className={`p-4 rounded-lg border ${
                                                    isDark ? 'border-purple-600 bg-purple-900/10' : 'border-purple-200 bg-purple-50'
                                                }`}>
                                                    <div className="flex items-center space-x-2 mb-3">
                                                        <div className={`w-3 h-3 rounded-full ${
                                                            isDark ? 'bg-purple-400' : 'bg-purple-500'
                                                        }`}></div>
                                                        <span className={`text-sm font-medium ${
                                                            isDark ? 'text-purple-300' : 'text-purple-700'
                                                        }`}>
                                                            Website Screenshot{session.secondaryUploads && session.secondaryUploads.length > 1 ? ` (${session.secondaryUploads.length})` : ''}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-start space-x-3">
                                                        <div className={`w-16 h-16 rounded-lg flex items-center justify-center ${
                                                            isDark ? 'bg-gray-700' : 'bg-gray-100'
                                                        }`}>
                                                            <Image className={isDark ? 'text-gray-500' : 'text-gray-400'} size={20} />
                                                        </div>
                                                        <div className="flex-1">
                                                            <h4 className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                                {session.secondaryUpload.original_filename}
                                                            </h4>
                                                            <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                {(session.secondaryUpload.file_size / 1024 / 1024).toFixed(2)} MB
                                                            </p>
                                                        </div>
                                                    </div>
                                                    {session.secondaryUpload.extracted_text && (
                                                        <div className={`mt-3 p-3 rounded border ${
                                                            isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                                                        }`}>
                                                            <div className="flex items-center justify-between mb-2">
                                                                <span className={`text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                                    Extracted Text
                                                                </span>
                                                                <FileText size={12} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                            </div>
                                                            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                                                {session.secondaryUpload.extracted_text.length > 120 
                                                                    ? `${session.secondaryUpload.extracted_text.substring(0, 120)}...`
                                                                    : session.secondaryUpload.extracted_text
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                            
                                            {/* Validation Results */}
                                            {session.validation && (
                                                <div className={`mt-6 p-4 rounded-lg border ${
                                                    isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                                                }`}>
                                                    <h4 className={`font-medium mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                        Validation Results
                                                    </h4>
                                                    <div className="grid grid-cols-3 gap-4">
                                                        <div className="text-center">
                                                            <div className={`text-2xl font-bold ${getStatusColor(session.accuracy)}`}>
                                                                {session.accuracy.toFixed(0)}%
                                                            </div>
                                                            <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                Accuracy
                                                            </div>
                                                        </div>
                                                        <div className="text-center">
                                                            <div className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                                {session.validation.total_fields || session.validation.total_lines || 0}
                                                            </div>
                                                            <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                Total Fields
                                                            </div>
                                                        </div>
                                                        <div className="text-center">
                                                            <div className={`text-2xl font-bold ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                                                                {session.validation.matched_fields || session.validation.matched_lines || 0}
                                                            </div>
                                                            <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                Matched
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        /* Standalone Upload */
                                        <div>
                                            <div className="flex items-center justify-between mb-4">
                                                <div className="flex items-center space-x-3">
                                                    <div>
                                                        <h3 className={`text-lg font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                            {getSessionName(session)}
                                                        </h3>
                                                        <div className="flex items-center space-x-1 mt-1">
                                                            <Calendar size={14} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                            <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                {date} at {time}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center space-x-2">
                                                    <button
                                                        onClick={() => handleViewSession(session)}
                                                        className={`p-2 rounded-lg transition-colors duration-150 ${
                                                            isDark 
                                                                ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                                                                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                                                        }`}
                                                        title="View session details"
                                                    >
                                                        <Eye size={16} />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteSession(session)}
                                                        className={`p-2 rounded-lg transition-colors duration-150 ${
                                                            isDark 
                                                                ? 'text-red-400 hover:text-red-300 hover:bg-red-900/20' 
                                                                : 'text-red-500 hover:text-red-700 hover:bg-red-50'
                                                        }`}
                                                        title="Delete session"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                            
                                            <div className={`p-4 rounded-lg border ${
                                                isDark ? 'border-gray-600 bg-gray-700/50' : 'border-gray-200 bg-gray-50'
                                            }`}>
                                                <div className="flex items-start space-x-4">
                                                    <div className={`w-20 h-20 rounded-lg flex items-center justify-center ${
                                                        isDark ? 'bg-gray-600' : 'bg-gray-100'
                                                    }`}>
                                                        <Image className={isDark ? 'text-gray-400' : 'text-gray-500'} size={24} />
                                                    </div>
                                                    <div className="flex-1">
                                                        <h4 className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                            {session.upload.original_filename}
                                                        </h4>
                                                        <div className="flex items-center space-x-4 mt-1">
                                                            <span className={`px-2 py-1 text-xs font-medium rounded ${
                                                                session.upload.image_type === 'main'
                                                                    ? isDark ? 'bg-blue-900/20 text-blue-400' : 'bg-blue-100 text-blue-700'
                                                                    : isDark ? 'bg-purple-900/20 text-purple-400' : 'bg-purple-100 text-purple-700'
                                                            }`}>
                                                                {session.upload.image_type === 'main' ? 'Util Screenshot' : 'Website Screenshot'}
                                                            </span>
                                                            <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                {(session.upload.file_size / 1024 / 1024).toFixed(2)} MB
                                                            </span>
                                                        </div>
                                                        {session.upload.extracted_text && (
                                                            <div className={`mt-3 p-3 rounded border ${
                                                                isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-100'
                                                            }`}>
                                                                <div className="flex items-center justify-between mb-2">
                                                                    <span className={`text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                                        Extracted Text
                                                                    </span>
                                                                    <FileText size={12} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                                </div>
                                                                <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                                                    {session.upload.extracted_text.length > 200 
                                                                        ? `${session.upload.extracted_text.substring(0, 200)}...`
                                                                        : session.upload.extracted_text
                                                                    }
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                    })}
                </div>
            )}
            
            {/* Session Details Modal */}
            <SessionDetailsModal 
                session={selectedSession}
                isOpen={isModalOpen}
                onClose={handleCloseModal}
                isDark={isDark}
            />
        </div>
    );
}

export default History;