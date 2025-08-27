import React from 'react';
import { CheckSquare, AlertTriangle } from 'lucide-react';
import GeminiValidationResults from '../../../components/GeminiValidationResults';

const ValidationSection = ({ 
  mainImages, 
  secondaryImages, 
  isValidating, 
  validationResult, 
  validationError,
  onValidate,
  onClearAll,
  isDark 
}) => {
  const hasMainImages = mainImages.length > 0;
  const hasSecondaryImages = secondaryImages.length > 0;
  const hasValidImages = hasMainImages && hasSecondaryImages && 
    mainImages[0]?.upload_id && secondaryImages[0]?.upload_id;

  return (
    <>
      {/* Action buttons when both image sections have images */}
      {hasMainImages && hasSecondaryImages && (
        <div className={`mt-8 pt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className="flex justify-center space-x-4">
            <button 
              onClick={onValidate}
              disabled={isValidating || !hasValidImages}
              className={`px-6 py-2 text-white font-medium rounded-lg transition-colors flex items-center space-x-2 ${
                isValidating || !hasValidImages
                  ? 'bg-gray-400 cursor-not-allowed'
                  : isDark 
                    ? 'bg-cyan-600 hover:bg-cyan-700' 
                    : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isValidating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <CheckSquare className="w-4 h-4" />
                  <span>Validate Transfer</span>
                </>
              )}
            </button>
            
            <button 
              onClick={onClearAll}
              className={`px-6 py-2 font-medium rounded-lg transition-colors ${
                isDark 
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              Clear All Images
            </button>
          </div>
        </div>
      )}

      {/* Validation Error Display */}
      {validationError && (
        <div className={`mt-8 p-4 rounded-lg border-l-4 border-red-500 ${
          isDark ? 'bg-red-900 bg-opacity-20' : 'bg-red-50'
        }`}>
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className={`text-sm font-medium ${isDark ? 'text-red-400' : 'text-red-800'}`}>
                Validation Error
              </h3>
              <p className={`mt-1 text-sm ${isDark ? 'text-red-300' : 'text-red-700'}`}>
                {validationError}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Validation Results */}
      <GeminiValidationResults 
        validationResult={validationResult}
        isDark={isDark}
        isLoading={isValidating}
      />
    </>
  );
};

export default ValidationSection;