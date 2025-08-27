import { X, Calendar, FileText, Image, CheckSquare, AlertTriangle, Clock } from 'lucide-react';

function SessionDetailsModal({ session, isOpen, onClose, isDark }) {
    if (!isOpen || !session) return null;
    
    // Debug: Log the session data structure
    console.log('SessionDetailsModal received session:', session);

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return {
            date: date.toLocaleDateString(),
            time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            full: date.toLocaleString()
        };
    };

    const getStatusIcon = (similarity) => {
        if (similarity >= 90) {
            return <CheckSquare className="text-green-500" size={20} />;
        } else if (similarity >= 70) {
            return <Clock className="text-yellow-500" size={20} />;
        } else {
            return <AlertTriangle className="text-red-500" size={20} />;
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

    const { full: fullDate } = formatDate(session.date);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Overlay */}
            <div 
                className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
                onClick={onClose}
            />
            
            {/* Modal */}
            <div className={`relative w-full max-w-6xl max-h-[90vh] overflow-y-auto rounded-xl shadow-2xl ${
                isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
            }`}>
                {/* Header */}
                <div className={`sticky top-0 flex items-center justify-between p-6 border-b ${
                    isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'
                }`}>
                    <div className="flex items-center space-x-3">
                        {session.type === 'comparison' ? (
                            <>
                                {getStatusIcon(session.accuracy)}
                                <div>
                                    <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        validation_session_{new Date(session.date).getTime()}
                                    </h2>
                                    <div className="flex items-center space-x-4 mt-1">
                                        <div className="flex items-center space-x-1">
                                            <Calendar size={14} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                            <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                {fullDate}
                                            </span>
                                        </div>
                                        <span className={`px-2 py-1 text-xs font-medium rounded border ${getStatusBadge(session.accuracy)}`}>
                                            {session.accuracy >= 90 ? 'Excellent' : session.accuracy >= 70 ? 'Good' : 'Needs Review'} ({session.accuracy.toFixed(0)}%)
                                        </span>
                                        <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                            {session.validation?.comparison_type === 'gemini_validation' ? 'Gemini AI' : 'Text Comparison'}
                                        </span>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <>
                                <Image className={isDark ? 'text-gray-400' : 'text-gray-500'} size={20} />
                                <div>
                                    <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        standalone_upload_{new Date(session.date).getTime()}
                                    </h2>
                                    <div className="flex items-center space-x-1 mt-1">
                                        <Calendar size={14} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                        <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                            {fullDate}
                                        </span>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className={`p-2 rounded-lg transition-colors duration-150 ${
                            isDark 
                                ? 'text-gray-400 hover:text-white hover:bg-gray-700' 
                                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                        }`}
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {session.type === 'comparison' ? (
                        /* Comparison Session Details */
                        <div className="space-y-6">
                            {/* Validation Summary */}
                            {session.validation && (
                                <div className={`p-6 rounded-lg border ${
                                    isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                                }`}>
                                    <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        Validation Results Summary
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                        <div className="text-center">
                                            <div className={`text-3xl font-bold ${getStatusColor(session.accuracy)}`}>
                                                {session.accuracy.toFixed(1)}%
                                            </div>
                                            <div className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                Overall Accuracy
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <div className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                {session.validation.total_fields || session.validation.total_lines || 0}
                                            </div>
                                            <div className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                Total Fields
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <div className={`text-3xl font-bold ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                                                {session.validation.matched_fields || session.validation.matched_lines || 0}
                                            </div>
                                            <div className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                Matched Fields
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <div className={`text-3xl font-bold ${isDark ? 'text-red-400' : 'text-red-600'}`}>
                                                {(session.validation.total_fields || session.validation.total_lines || 0) - (session.validation.matched_fields || session.validation.matched_lines || 0)}
                                            </div>
                                            <div className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                Mismatched Fields
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Detailed Field Matching */}
                            {session.validation && session.validation.validation_result && (
                                <div className={`p-6 rounded-lg border ${
                                    isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                                }`}>
                                    <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        Field Matching Details
                                    </h3>
                                    
                                    {/* Field Matches - Handle both Gemini and Simple Text formats */}
                                    {((session.validation.validation_result.matched_data && session.validation.validation_result.matched_data.length > 0) || 
                                      (session.validation.validation_result.text_matches && session.validation.validation_result.text_matches.length > 0)) && (
                                        <div className="space-y-4">
                                            <h4 className={`font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                Matched Fields ({session.validation.validation_result.matched_data?.length || session.validation.validation_result.text_matches?.length || 0})
                                            </h4>
                                            <div className="space-y-3 max-h-96 overflow-y-auto">
                                                {/* Gemini Validation Format */}
                                                {session.validation.validation_result.matched_data && session.validation.validation_result.matched_data.map((match, index) => (
                                                    <div key={index} className={`p-4 rounded-lg border ${
                                                        match.match === 'exact' 
                                                            ? isDark ? 'border-green-600 bg-green-900/10' : 'border-green-200 bg-green-50'
                                                            : match.match === 'equivalent'
                                                            ? isDark ? 'border-blue-600 bg-blue-900/10' : 'border-blue-200 bg-blue-50'
                                                            : isDark ? 'border-yellow-600 bg-yellow-900/10' : 'border-yellow-200 bg-yellow-50'
                                                    }`}>
                                                        <div className="flex items-center justify-between mb-3">
                                                            <div className="flex items-center space-x-2">
                                                                <span className={`text-xs font-medium px-2 py-1 rounded ${
                                                                    match.match === 'exact'
                                                                        ? isDark ? 'bg-green-800 text-green-300' : 'bg-green-100 text-green-800'
                                                                        : match.match === 'equivalent'
                                                                        ? isDark ? 'bg-blue-800 text-blue-300' : 'bg-blue-100 text-blue-800'
                                                                        : isDark ? 'bg-yellow-800 text-yellow-300' : 'bg-yellow-100 text-yellow-800'
                                                                }`}>
                                                                    {match.match} match
                                                                </span>
                                                                <span className={`text-sm font-medium ${
                                                                    match.confidence >= 90
                                                                        ? isDark ? 'text-green-400' : 'text-green-600'
                                                                        : match.confidence >= 70
                                                                        ? isDark ? 'text-yellow-400' : 'text-yellow-600'
                                                                        : isDark ? 'text-red-400' : 'text-red-600'
                                                                }`}>
                                                                    {match.confidence}% confidence
                                                                </span>
                                                            </div>
                                                            <span className={`text-xs font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                                                {match.field}
                                                            </span>
                                                        </div>
                                                        
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                            <div>
                                                                <div className={`text-xs font-medium mb-1 ${
                                                                    isDark ? 'text-blue-300' : 'text-blue-700'
                                                                }`}>
                                                                    Source (Util Screenshot)
                                                                </div>
                                                                <div className={`p-2 rounded text-xs font-mono ${
                                                                    isDark ? 'bg-gray-800 text-gray-300' : 'bg-white text-gray-700'
                                                                }`}>
                                                                    "{match.source_value || 'N/A'}"
                                                                </div>
                                                            </div>
                                                            <div>
                                                                <div className={`text-xs font-medium mb-1 ${
                                                                    isDark ? 'text-purple-300' : 'text-purple-700'
                                                                }`}>
                                                                    Destination (Website Screenshot)
                                                                </div>
                                                                <div className={`p-2 rounded text-xs font-mono ${
                                                                    isDark ? 'bg-gray-800 text-gray-300' : 'bg-white text-gray-700'
                                                                }`}>
                                                                    "{match.dest_value || 'N/A'}"
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                                
                                                {/* Simple Text Validation Format */}
                                                {session.validation.validation_result.text_matches && session.validation.validation_result.text_matches.map((match, index) => (
                                                    <div key={index} className={`p-4 rounded-lg border ${
                                                        match.match_type === 'exact' 
                                                            ? isDark ? 'border-green-600 bg-green-900/10' : 'border-green-200 bg-green-50'
                                                            : match.match_type === 'partial'
                                                            ? isDark ? 'border-yellow-600 bg-yellow-900/10' : 'border-yellow-200 bg-yellow-50'
                                                            : isDark ? 'border-red-600 bg-red-900/10' : 'border-red-200 bg-red-50'
                                                    }`}>
                                                        <div className="flex items-center justify-between mb-2">
                                                            <div className="flex items-center space-x-2">
                                                                <span className={`text-xs font-medium px-2 py-1 rounded ${
                                                                    match.match_type === 'exact'
                                                                        ? isDark ? 'bg-green-800 text-green-300' : 'bg-green-100 text-green-800'
                                                                        : match.match_type === 'partial'
                                                                        ? isDark ? 'bg-yellow-800 text-yellow-300' : 'bg-yellow-100 text-yellow-800'
                                                                        : isDark ? 'bg-red-800 text-red-300' : 'bg-red-100 text-red-800'
                                                                }`}>
                                                                    {match.match_type} match
                                                                </span>
                                                                <span className={`text-sm font-medium ${
                                                                    match.match_score >= 90
                                                                        ? isDark ? 'text-green-400' : 'text-green-600'
                                                                        : match.match_score >= 70
                                                                        ? isDark ? 'text-yellow-400' : 'text-yellow-600'
                                                                        : isDark ? 'text-red-400' : 'text-red-600'
                                                                }`}>
                                                                    {match.match_score}% similarity
                                                                </span>
                                                            </div>
                                                            {match.line_number && (
                                                                <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                                    Line {match.line_number}
                                                                </span>
                                                            )}
                                                        </div>
                                                        
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                            <div>
                                                                <div className={`text-xs font-medium mb-1 ${
                                                                    isDark ? 'text-blue-300' : 'text-blue-700'
                                                                }`}>
                                                                    Source (Util Screenshot)
                                                                </div>
                                                                <div className={`p-2 rounded text-xs font-mono ${
                                                                    isDark ? 'bg-gray-800 text-gray-300' : 'bg-white text-gray-700'
                                                                }`}>
                                                                    "{match.source_text}"
                                                                </div>
                                                            </div>
                                                            <div>
                                                                <div className={`text-xs font-medium mb-1 ${
                                                                    isDark ? 'text-purple-300' : 'text-purple-700'
                                                                }`}>
                                                                    Destination (Website Screenshot)
                                                                </div>
                                                                <div className={`p-2 rounded text-xs font-mono ${
                                                                    isDark ? 'bg-gray-800 text-gray-300' : 'bg-white text-gray-700'
                                                                }`}>
                                                                    "{match.dest_text}"
                                                                </div>
                                                            </div>
                                                        </div>
                                                        
                                                        {match.issues && match.issues.length > 0 && (
                                                            <div className="mt-3">
                                                                <div className={`text-xs font-medium mb-1 ${
                                                                    isDark ? 'text-yellow-300' : 'text-yellow-700'
                                                                }`}>
                                                                    Issues:
                                                                </div>
                                                                <ul className={`text-xs space-y-1 ${
                                                                    isDark ? 'text-gray-400' : 'text-gray-600'
                                                                }`}>
                                                                    {match.issues.map((issue, issueIndex) => (
                                                                        <li key={issueIndex} className="flex items-start space-x-2">
                                                                            <span className="text-yellow-500">•</span>
                                                                            <span>{issue}</span>
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Missing Data and Incorrect Data - Handle both formats */}
                                    {((session.validation.validation_result.missing_data && session.validation.validation_result.missing_data.length > 0) ||
                                      (session.validation.validation_result.incorrect_data && session.validation.validation_result.incorrect_data.length > 0) ||
                                      (session.validation.validation_result.missing_lines > 0) ||
                                      (session.validation.validation_result.extra_lines > 0)) && (
                                        <div className="mt-6 pt-6 border-t border-gray-600">
                                            <h4 className={`font-medium mb-4 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                Missing & Incorrect Fields
                                            </h4>
                                            
                                            {/* Gemini Format - Missing Data */}
                                            {session.validation.validation_result.missing_data && session.validation.validation_result.missing_data.length > 0 && (
                                                <div className="mb-6">
                                                    <h5 className={`font-medium mb-3 ${isDark ? 'text-red-300' : 'text-red-700'}`}>
                                                        Missing Fields ({session.validation.validation_result.missing_data.length})
                                                    </h5>
                                                    <div className="space-y-2">
                                                        {session.validation.validation_result.missing_data.map((missing, index) => (
                                                            <div key={index} className={`p-3 rounded-lg border ${
                                                                isDark ? 'border-red-600 bg-red-900/10' : 'border-red-200 bg-red-50'
                                                            }`}>
                                                                <div className="flex items-center justify-between mb-2">
                                                                    <span className={`text-sm font-medium ${isDark ? 'text-red-300' : 'text-red-700'}`}>
                                                                        {missing.field}
                                                                    </span>
                                                                    <span className={`text-xs px-2 py-1 rounded ${
                                                                        isDark ? 'bg-red-800 text-red-300' : 'bg-red-100 text-red-800'
                                                                    }`}>
                                                                        missing
                                                                    </span>
                                                                </div>
                                                                <div className="text-xs space-y-1">
                                                                    <div className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                                                        <strong>Source:</strong> {missing.source_value || 'Not present'}
                                                                    </div>
                                                                    <div className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                                                        <strong>Destination:</strong> {missing.dest_value || 'Not present'}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {/* Gemini Format - Incorrect Data */}
                                            {session.validation.validation_result.incorrect_data && session.validation.validation_result.incorrect_data.length > 0 && (
                                                <div className="mb-6">
                                                    <h5 className={`font-medium mb-3 ${isDark ? 'text-red-300' : 'text-red-700'}`}>
                                                        Incorrect Fields ({session.validation.validation_result.incorrect_data.length})
                                                    </h5>
                                                    <div className="space-y-2">
                                                        {session.validation.validation_result.incorrect_data.map((incorrect, index) => (
                                                            <div key={index} className={`p-3 rounded-lg border ${
                                                                isDark ? 'border-red-600 bg-red-900/10' : 'border-red-200 bg-red-50'
                                                            }`}>
                                                                <div className="flex items-center justify-between mb-2">
                                                                    <span className={`text-sm font-medium ${isDark ? 'text-red-300' : 'text-red-700'}`}>
                                                                        {incorrect.field}
                                                                    </span>
                                                                    <span className={`text-xs px-2 py-1 rounded ${
                                                                        isDark ? 'bg-red-800 text-red-300' : 'bg-red-100 text-red-800'
                                                                    }`}>
                                                                        incorrect
                                                                    </span>
                                                                </div>
                                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                    <div>
                                                                        <div className={`text-xs font-medium mb-1 ${
                                                                            isDark ? 'text-blue-300' : 'text-blue-700'
                                                                        }`}>
                                                                            Source
                                                                        </div>
                                                                        <div className={`p-2 rounded text-xs font-mono ${
                                                                            isDark ? 'bg-gray-800 text-gray-300' : 'bg-white text-gray-700'
                                                                        }`}>
                                                                            "{incorrect.source_value || 'N/A'}"
                                                                        </div>
                                                                    </div>
                                                                    <div>
                                                                        <div className={`text-xs font-medium mb-1 ${
                                                                            isDark ? 'text-purple-300' : 'text-purple-700'
                                                                        }`}>
                                                                            Destination
                                                                        </div>
                                                                        <div className={`p-2 rounded text-xs font-mono ${
                                                                            isDark ? 'bg-gray-800 text-gray-300' : 'bg-white text-gray-700'
                                                                        }`}>
                                                                            "{incorrect.dest_value || 'N/A'}"
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {/* Simple Text Format - Missing and Extra Lines */}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                {session.validation.validation_result.missing_lines > 0 && (
                                                    <div className={`p-4 rounded-lg border ${
                                                        isDark ? 'border-red-600 bg-red-900/10' : 'border-red-200 bg-red-50'
                                                    }`}>
                                                        <h5 className={`font-medium mb-2 ${
                                                            isDark ? 'text-red-300' : 'text-red-700'
                                                        }`}>
                                                            Missing Lines ({session.validation.validation_result.missing_lines})
                                                        </h5>
                                                        <p className={`text-xs ${
                                                            isDark ? 'text-gray-400' : 'text-gray-600'
                                                        }`}>
                                                            Lines present in util screenshot but not found in website screenshot
                                                        </p>
                                                    </div>
                                                )}
                                                
                                                {session.validation.validation_result.extra_lines > 0 && (
                                                    <div className={`p-4 rounded-lg border ${
                                                        isDark ? 'border-orange-600 bg-orange-900/10' : 'border-orange-200 bg-orange-50'
                                                    }`}>
                                                        <h5 className={`font-medium mb-2 ${
                                                            isDark ? 'text-orange-300' : 'text-orange-700'
                                                        }`}>
                                                            Extra Lines ({session.validation.validation_result.extra_lines})
                                                        </h5>
                                                        <p className={`text-xs ${
                                                            isDark ? 'text-gray-400' : 'text-gray-600'
                                                        }`}>
                                                            Lines present in website screenshot but not found in util screenshot
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Recommendations */}
                                    {session.validation.validation_result.recommendations && session.validation.validation_result.recommendations.length > 0 && (
                                        <div className="mt-6 pt-6 border-t border-gray-600">
                                            <h4 className={`font-medium mb-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                Recommendations
                                            </h4>
                                            <ul className={`space-y-2 text-sm ${
                                                isDark ? 'text-gray-400' : 'text-gray-600'
                                            }`}>
                                                {session.validation.validation_result.recommendations.map((rec, index) => (
                                                    <li key={index} className="flex items-start space-x-2">
                                                        <span className={isDark ? 'text-blue-400' : 'text-blue-500'}>•</span>
                                                        <span>{rec}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Upload Comparison */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Main Upload */}
                                <div className={`p-6 rounded-lg border ${
                                    isDark ? 'border-blue-600 bg-blue-900/10' : 'border-blue-200 bg-blue-50'
                                }`}>
                                    <div className="flex items-center space-x-2 mb-4">
                                        <div className={`w-4 h-4 rounded-full ${
                                            isDark ? 'bg-blue-400' : 'bg-blue-500'
                                        }`}></div>
                                        <h4 className={`text-lg font-semibold ${ 
                                            isDark ? 'text-blue-300' : 'text-blue-700'
                                        }`}>Util Screenshot</h4>
                                    </div>
                                    
                                    <div className="space-y-4">
                                        {/* Image Info */}
                                        <div className="flex items-start space-x-4">
                                            <div className={`w-20 h-20 rounded-lg flex items-center justify-center ${
                                                isDark ? 'bg-gray-700' : 'bg-gray-100'
                                            }`}>
                                                <Image className={isDark ? 'text-gray-500' : 'text-gray-400'} size={24} />
                                            </div>
                                            <div className="flex-1">
                                                <h5 className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                    {session.mainUpload.original_filename}
                                                </h5>
                                                <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                    Size: {(session.mainUpload.file_size / 1024 / 1024).toFixed(2)} MB
                                                </p>
                                                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                    Type: {session.mainUpload.mime_type || 'image/*'}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Extracted Text */}
                                        {session.mainUpload.extracted_text && (
                                            <div className={`p-4 rounded-lg border ${
                                                isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                                            }`}>
                                                <div className="flex items-center space-x-2 mb-3">
                                                    <FileText size={16} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                    <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                        Extracted Text ({session.mainUpload.extracted_text.length} characters)
                                                    </span>
                                                </div>
                                                <div className={`max-h-96 overflow-y-auto p-3 rounded border ${
                                                    isDark ? 'border-gray-600 bg-gray-800' : 'border-gray-200 bg-white'
                                                }`}>
                                                    <pre className={`text-xs leading-relaxed whitespace-pre-wrap font-mono ${
                                                        isDark ? 'text-gray-300' : 'text-gray-700'
                                                    }`}>
                                                        {session.mainUpload.extracted_text}
                                                    </pre>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Secondary Upload */}
                                <div className={`p-6 rounded-lg border ${
                                    isDark ? 'border-purple-600 bg-purple-900/10' : 'border-purple-200 bg-purple-50'
                                }`}>
                                    <div className="flex items-center space-x-2 mb-4">
                                        <div className={`w-4 h-4 rounded-full ${
                                            isDark ? 'bg-purple-400' : 'bg-purple-500'
                                        }`}></div>
                                        <h4 className={`text-lg font-semibold ${ 
                                            isDark ? 'text-purple-300' : 'text-purple-700'
                                        }`}>Website Screenshot</h4>
                                    </div>
                                    
                                    <div className="space-y-4">
                                        {/* Image Info */}
                                        <div className="flex items-start space-x-4">
                                            <div className={`w-20 h-20 rounded-lg flex items-center justify-center ${
                                                isDark ? 'bg-gray-700' : 'bg-gray-100'
                                            }`}>
                                                <Image className={isDark ? 'text-gray-500' : 'text-gray-400'} size={24} />
                                            </div>
                                            <div className="flex-1">
                                                <h5 className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                                    {session.secondaryUpload.original_filename}
                                                </h5>
                                                <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                    Size: {(session.secondaryUpload.file_size / 1024 / 1024).toFixed(2)} MB
                                                </p>
                                                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                    Type: {session.secondaryUpload.mime_type || 'image/*'}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Extracted Text */}
                                        {session.secondaryUpload.extracted_text && (
                                            <div className={`p-4 rounded-lg border ${
                                                isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                                            }`}>
                                                <div className="flex items-center space-x-2 mb-3">
                                                    <FileText size={16} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                    <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                        Extracted Text ({session.secondaryUpload.extracted_text.length} characters)
                                                    </span>
                                                </div>
                                                <div className={`max-h-96 overflow-y-auto p-3 rounded border ${
                                                    isDark ? 'border-gray-600 bg-gray-800' : 'border-gray-200 bg-white'
                                                }`}>
                                                    <pre className={`text-xs leading-relaxed whitespace-pre-wrap font-mono ${
                                                        isDark ? 'text-gray-300' : 'text-gray-700'
                                                    }`}>
                                                        {session.secondaryUpload.extracted_text}
                                                    </pre>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        /* Standalone Upload Details */
                        <div className={`p-6 rounded-lg border ${
                            isDark ? 'border-gray-600 bg-gray-700/50' : 'border-gray-200 bg-gray-50'
                        }`}>
                            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                Upload Details
                            </h3>
                            
                            <div className="flex items-start space-x-6">
                                <div className={`w-24 h-24 rounded-lg flex items-center justify-center ${
                                    isDark ? 'bg-gray-600' : 'bg-gray-100'
                                }`}>
                                    <Image className={isDark ? 'text-gray-400' : 'text-gray-500'} size={32} />
                                </div>
                                
                                <div className="flex-1 space-y-4">
                                    <div>
                                        <h4 className={`text-lg font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                            {session.upload.original_filename}
                                        </h4>
                                        <div className="flex items-center space-x-4 mt-2">
                                            <span className={`px-3 py-1 text-sm font-medium rounded ${ 
                                                session.upload.image_type === 'main'
                                                    ? isDark ? 'bg-blue-900/20 text-blue-400' : 'bg-blue-100 text-blue-700'
                                                    : isDark ? 'bg-purple-900/20 text-purple-400' : 'bg-purple-100 text-purple-700'
                                            }`}>
                                                {session.upload.image_type === 'main' ? 'Util Screenshot' : 'Website Screenshot'}
                                            </span>
                                            <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                {(session.upload.file_size / 1024 / 1024).toFixed(2)} MB
                                            </span>
                                            <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                                {session.upload.mime_type || 'image/*'}
                                            </span>
                                        </div>
                                    </div>

                                    {session.upload.extracted_text && (
                                        <div className={`p-4 rounded-lg border ${
                                            isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-100'
                                        }`}>
                                            <div className="flex items-center space-x-2 mb-3">
                                                <FileText size={16} className={isDark ? 'text-gray-400' : 'text-gray-500'} />
                                                <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                                                    Extracted Text ({session.upload.extracted_text.length} characters)
                                                </span>
                                            </div>
                                            <div className={`max-h-96 overflow-y-auto p-3 rounded border ${
                                                isDark ? 'border-gray-600 bg-gray-800' : 'border-gray-200 bg-white'
                                            }`}>
                                                <pre className={`text-sm leading-relaxed whitespace-pre-wrap font-mono ${
                                                    isDark ? 'text-gray-300' : 'text-gray-700'
                                                }`}>
                                                    {session.upload.extracted_text}
                                                </pre>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default SessionDetailsModal;