import React from 'react';
import { X, Copy, FileText } from 'lucide-react';

const TextModal = ({ isOpen, onClose, title, text, isDark }) => {
  if (!isOpen) return null;

  const handleCopyText = async () => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
      alert('Text copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy text:', err);
      alert('Failed to copy text');
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div 
        className={`max-w-4xl w-full max-h-[80vh] rounded-lg shadow-xl ${
          isDark ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'
        }`}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`flex items-center justify-between p-6 border-b ${
          isDark ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <div className="flex items-center space-x-3">
            <FileText className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-500'}`} />
            <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {title} - Extracted Text
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyText}
              disabled={!text}
              className={`p-2 rounded-lg transition-colors ${
                !text 
                  ? 'opacity-50 cursor-not-allowed'
                  : isDark
                    ? 'hover:bg-gray-700 text-gray-300 hover:text-white'
                    : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
              title="Copy text"
            >
              <Copy className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className={`p-2 rounded-lg transition-colors ${
                isDark
                  ? 'hover:bg-gray-700 text-gray-300 hover:text-white'
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className={`rounded-lg border p-4 max-h-96 overflow-y-auto ${
            isDark 
              ? 'border-gray-600 bg-gray-700' 
              : 'border-gray-200 bg-gray-50'
          }`}>
            {text ? (
              <pre className={`whitespace-pre-wrap font-mono text-sm leading-relaxed ${
                isDark ? 'text-gray-200' : 'text-gray-800'
              }`}>
                {text}
              </pre>
            ) : (
              <div className="text-center py-8">
                <FileText className={`w-12 h-12 mx-auto mb-3 opacity-50 ${
                  isDark ? 'text-gray-500' : 'text-gray-400'
                }`} />
                <p className={`text-lg font-medium ${
                  isDark ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  No text extracted
                </p>
                <p className={`text-sm mt-1 ${
                  isDark ? 'text-gray-500' : 'text-gray-400'
                }`}>
                  The text extraction process may have failed or the image may not contain readable text.
                </p>
              </div>
            )}
          </div>

          {/* Text Stats */}
          {text && (
            <div className={`mt-4 text-xs flex items-center justify-between ${
              isDark ? 'text-gray-400' : 'text-gray-500'
            }`}>
              <span>
                Characters: {text.length.toLocaleString()}
              </span>
              <span>
                Words: {text.split(/\s+/).filter(word => word.length > 0).length.toLocaleString()}
              </span>
              <span>
                Lines: {text.split('\n').length.toLocaleString()}
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t flex justify-end ${
          isDark ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <button
            onClick={onClose}
            className={`px-4 py-2 rounded-lg transition-colors ${
              isDark
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default TextModal;