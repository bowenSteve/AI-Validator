import React, { useState } from 'react';
import { Eye } from 'lucide-react';
import TextModal from './TextModal';

const CombinedImageDataCard = ({ images, title, isDark, onViewText }) => {
  // Combine extracted text from all images with line separators
  const combinedText = images
    .filter(img => img.extracted_text)
    .map(img => img.extracted_text)
    .join('\n---\n');
  
  // Get overall processing status
  const allProcessed = images.every(img => img.gemini_processing?.success);
  const anyFailed = images.some(img => img.gemini_processing?.success === false);
  
  // Calculate total file size
  const totalSize = images.reduce((sum, img) => sum + (img.file_size || 0), 0);
  
  return (
    <div className={`p-4 rounded-lg border ${
      isDark 
        ? 'border-gray-600 bg-gray-800' 
        : 'border-gray-200 bg-gray-50'
    }`}>
      <h4 className={`text-md font-medium mb-3 ${isDark ? 'text-cyan-300' : 'text-blue-500'}`}>
        {title} ({images.length} image{images.length > 1 ? 's' : ''})
      </h4>
      
      <div className="space-y-3">
        <div>
          <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            Combined File Information:
          </label>
          <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <p>Files: {images.map(img => img.name).join(', ')}</p>
            <p>Total Size: {(totalSize / 1024 / 1024).toFixed(2)} MB</p>
            <p>Upload IDs: {images.map(img => img.upload_id || 'N/A').join(', ')}</p>
            <p>Latest Upload: {images.length > 0 ? new Date(Math.max(...images.map(img => new Date(img.uploaded_at)))).toLocaleString() : 'N/A'}</p>
          </div>
        </div>
        
        <div>
          <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            Processing Status:
          </label>
          <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {allProcessed ? (
              <p className="text-green-500">● All images processed successfully</p>
            ) : anyFailed ? (
              <p className="text-red-500">● Some images failed processing</p>
            ) : (
              <p className="text-yellow-500">● Processing in progress or status unknown</p>
            )}
          </div>
        </div>
        
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              Combined Extracted Text:
            </label>
            {combinedText && (
              <button
                onClick={() => onViewText({ extracted_text: combinedText }, title)}
                className={`flex items-center space-x-1 px-2 py-1 text-xs rounded transition-colors ${
                  isDark
                    ? 'bg-cyan-600 hover:bg-cyan-700 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                <Eye className="w-3 h-3" />
                <span>View Text</span>
              </button>
            )}
          </div>
          <div className={`p-3 rounded border text-xs max-h-32 overflow-y-auto ${
            isDark 
              ? 'border-gray-600 bg-gray-700 text-gray-300' 
              : 'border-gray-200 bg-white text-gray-700'
          }`}>
            {combinedText ? (
              <div>
                <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed line-clamp-4">
                  {combinedText.length > 200 
                    ? `${combinedText.substring(0, 200)}...`
                    : combinedText
                  }
                </pre>
                {combinedText.length > 200 && (
                  <button
                    onClick={() => onViewText({ extracted_text: combinedText }, title)}
                    className={`mt-2 text-xs underline ${
                      isDark ? 'text-cyan-400 hover:text-cyan-300' : 'text-blue-500 hover:text-blue-600'
                    }`}
                  >
                    View full text ({combinedText.length} characters)
                  </button>
                )}
              </div>
            ) : (
              <p className={`italic ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                {anyFailed 
                  ? 'Some text extraction failed' 
                  : 'No text extracted or processing in progress...'}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};


const ImageDataSection = ({ mainImages, secondaryImages, isDark }) => {
  const [modalState, setModalState] = useState({
    isOpen: false,
    image: null,
    title: ''
  });

  const handleViewText = (image, title) => {
    setModalState({
      isOpen: true,
      image,
      title
    });
  };

  const handleCloseModal = () => {
    setModalState({
      isOpen: false,
      image: null,
      title: ''
    });
  };

  if (mainImages.length === 0 && secondaryImages.length === 0) {
    return null;
  }

  return (
    <div className={`mt-8 pt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
      <h2 className={`text-xl font-semibold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
        Image Data Fields
      </h2>
      
      <div className="grid md:grid-cols-2 gap-8">
        {/* Main Images Data - Left Side */}
        <div className="space-y-4">
          {mainImages.length > 0 && (
            <CombinedImageDataCard
              images={mainImages}
              title="Util Screenshots Data"
              isDark={isDark}
              onViewText={handleViewText}
            />
          )}
        </div>

        {/* Secondary Images Data - Right Side */}
        <div className="space-y-4">
          {secondaryImages.length > 0 && (
            <CombinedImageDataCard
              images={secondaryImages}
              title="Website Screenshots Data"
              isDark={isDark}
              onViewText={handleViewText}
            />
          )}
        </div>
      </div>

      {/* Text Modal */}
      <TextModal
        isOpen={modalState.isOpen}
        onClose={handleCloseModal}
        title={modalState.title}
        text={modalState.image?.extracted_text || ''}
        isDark={isDark}
      />
    </div>
  );
};

export default ImageDataSection;