import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, TrendingUp, Target, BarChart3 } from 'lucide-react';

const GeminiValidationResults = ({ validationResult, isDark, isLoading }) => {
  if (isLoading) {
    return (
      <div className={`mt-8 p-6 rounded-lg border ${
        isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className={`ml-3 text-lg ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            Analyzing data transfer...
          </span>
        </div>
      </div>
    );
  }

  if (!validationResult) {
    return null;
  }

  const getScoreColor = (score) => {
    if (score >= 90) return isDark ? 'text-green-400' : 'text-green-600';
    if (score >= 70) return isDark ? 'text-yellow-400' : 'text-yellow-600';
    return isDark ? 'text-red-400' : 'text-red-600';
  };

  const getScoreIcon = (score) => {
    if (score >= 90) return <CheckCircle className="w-6 h-6" />;
    if (score >= 70) return <AlertTriangle className="w-6 h-6" />;
    return <XCircle className="w-6 h-6" />;
  };

  const getMatchIcon = (matchType) => {
    switch (matchType) {
      case 'exact':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'equivalent':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'partial':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getMatchLabel = (matchType) => {
    const labels = {
      'exact': 'Exact Match',
      'equivalent': 'Equivalent',
      'partial': 'Partial Match',
      'different': 'Different'
    };
    return labels[matchType] || matchType;
  };

  return (
    <div className={`mt-8 space-y-6`}>
      {/* Header with Score */}
      <div className={`p-6 rounded-lg border ${
        isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Validation Results
          </h2>
          <div className={`flex items-center space-x-3 ${getScoreColor(validationResult.accuracy_score)}`}>
            {getScoreIcon(validationResult.accuracy_score)}
            <span className="text-3xl font-bold">
              {validationResult.accuracy_score}%
            </span>
          </div>
        </div>

        {/* Summary */}
        <div className={`p-4 rounded-lg ${
          isDark ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <strong>Analysis:</strong> {validationResult.summary}
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div className={`p-3 rounded border ${
            isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
          }`}>
            <div className="flex items-center space-x-2">
              <Target className={`w-4 h-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
              <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                Fields Found
              </span>
            </div>
            <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {validationResult.total_fields_identified || 0}
            </p>
          </div>

          <div className={`p-3 rounded border ${
            isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
          }`}>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                Correct
              </span>
            </div>
            <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {validationResult.fields_transferred_correctly || validationResult.matched_data?.length || 0}
            </p>
          </div>

          <div className={`p-3 rounded border ${
            isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
          }`}>
            <div className="flex items-center space-x-2">
              <XCircle className="w-4 h-4 text-red-500" />
              <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                Missing
              </span>
            </div>
            <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {validationResult.missing_data?.length || 0}
            </p>
          </div>

          <div className={`p-3 rounded border ${
            isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
          }`}>
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-purple-500" />
              <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                Confidence
              </span>
            </div>
            <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {validationResult.confidence || 0}%
            </p>
          </div>
        </div>
      </div>

      {/* Field-by-Field Analysis */}
      {validationResult.matched_data && validationResult.matched_data.length > 0 && (
        <div className={`p-6 rounded-lg border ${
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Matched Data Fields
          </h3>
          
          <div className="space-y-4">
            {validationResult.matched_data.map((match, index) => (
              <div key={index} className={`p-4 rounded border ${
                isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getMatchIcon(match.match)}
                    <div>
                      <h4 className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        {match.field}
                      </h4>
                      <span className={`text-sm px-2 py-1 rounded ${
                        match.match === 'exact' ? 'bg-green-100 text-green-800' :
                        match.match === 'equivalent' ? 'bg-green-100 text-green-800' :
                        match.match === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {getMatchLabel(match.match)}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${getScoreColor(match.confidence || 100)}`}>
                      {match.confidence || 100}%
                    </div>
                  </div>
                </div>

                {/* Value Comparison */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className={`text-xs font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      Source:
                    </label>
                    <p className={`text-sm p-2 rounded border font-mono ${
                      isDark ? 'bg-gray-800 border-gray-600 text-gray-200' : 'bg-white border-gray-200 text-gray-800'
                    }`}>
                      {match.source_value}
                    </p>
                  </div>
                  <div>
                    <label className={`text-xs font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      Destination:
                    </label>
                    <p className={`text-sm p-2 rounded border font-mono ${
                      isDark ? 'bg-gray-800 border-gray-600 text-gray-200' : 'bg-white border-gray-200 text-gray-800'
                    }`}>
                      {match.dest_value}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing Data */}
      {validationResult.missing_data && validationResult.missing_data.length > 0 && (
        <div className={`p-6 rounded-lg border border-red-200 ${
          isDark ? 'bg-red-900 bg-opacity-20' : 'bg-red-50'
        }`}>
          <h3 className={`text-xl font-semibold mb-4 text-red-600`}>
            Missing Data
          </h3>
          <div className="space-y-3">
            {validationResult.missing_data.map((missing, index) => (
              <div key={index} className={`flex items-start space-x-3`}>
                <XCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className={`font-medium text-red-700`}>{missing.field}</p>
                  <p className={`text-sm text-red-600`}>{missing.value}</p>
                  <p className={`text-xs text-red-500`}>{missing.issue}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Incorrect Data */}
      {validationResult.incorrect_data && validationResult.incorrect_data.length > 0 && (
        <div className={`p-6 rounded-lg border border-orange-200 ${
          isDark ? 'bg-orange-900 bg-opacity-20' : 'bg-orange-50'
        }`}>
          <h3 className={`text-xl font-semibold mb-4 text-orange-600`}>
            Incorrect Data
          </h3>
          <div className="space-y-3">
            {validationResult.incorrect_data.map((incorrect, index) => (
              <div key={index} className={`flex items-start space-x-3`}>
                <AlertTriangle className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className={`font-medium text-orange-700`}>{incorrect.field}</p>
                  <div className="grid md:grid-cols-2 gap-2 mt-1">
                    <p className={`text-sm text-orange-600`}>
                      <strong>Expected:</strong> {incorrect.source_value}
                    </p>
                    <p className={`text-sm text-orange-600`}>
                      <strong>Found:</strong> {incorrect.dest_value}
                    </p>
                  </div>
                  <p className={`text-xs text-orange-500`}>{incorrect.issue}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      {validationResult.recommendations && validationResult.recommendations.length > 0 && (
        <div className={`p-6 rounded-lg border ${
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <h3 className={`text-xl font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Recommendations
          </h3>
          <ul className="space-y-3">
            {validationResult.recommendations.map((recommendation, index) => (
              <li key={index} className={`flex items-start space-x-3`}>
                <TrendingUp className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                  isDark ? 'text-cyan-400' : 'text-blue-600'
                }`} />
                <span className={`${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  {recommendation}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Transfer Status Badge */}
      <div className="flex justify-center">
        <div className={`px-6 py-3 rounded-full text-center ${
          validationResult.is_successful_transfer
            ? isDark 
              ? 'bg-green-900 border-2 border-green-600' 
              : 'bg-green-100 border-2 border-green-500'
            : isDark 
              ? 'bg-red-900 border-2 border-red-600' 
              : 'bg-red-100 border-2 border-red-500'
        }`}>
          <div className="flex items-center space-x-2">
            {validationResult.is_successful_transfer ? 
              <CheckCircle className="w-5 h-5 text-green-600" /> : 
              <XCircle className="w-5 h-5 text-red-600" />
            }
            <span className={`font-semibold ${
              validationResult.is_successful_transfer 
                ? 'text-green-700' 
                : 'text-red-700'
            }`}>
              {validationResult.is_successful_transfer 
                ? 'Data Transfer Successful' 
                : 'Data Transfer Needs Review'
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeminiValidationResults;