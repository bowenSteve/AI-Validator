import React, { useState } from 'react';
import { Eye } from 'lucide-react';
import TextModal from './TextModal';

const ImageCard = ({ image, index, title, isDark, onViewText }) => (
  <div className={`p-4 rounded-lg border ${
    isDark 
      ? 'border-gray-600 bg-gray-800' 
      : 'border-gray-200 bg-gray-50'
  }`}>
    <h4 className={`text-md font-medium mb-3 ${isDark ? 'text-cyan-300' : 'text-blue-500'}`}>
      {title} #{index + 1}
    </h4>
    
    <div className="space-y-3">
      <div>
        <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          File Information:
        </label>
        <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <p>Name: {image.name}</p>
          <p>Size: {(image.file_size / 1024 / 1024).toFixed(2)} MB</p>
          <p>Upload ID: {image.upload_id || 'N/A'}</p>
          <p>Type: {image.type}</p>
          <p>Uploaded: {new Date(image.uploaded_at).toLocaleString()}</p>
        </div>
      </div>
      
      <div>
        <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Processing Status:
        </label>
        <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          {image.gemini_processing ? (
            <div className="space-y-1">
              <p className={image.gemini_processing.success ? 'text-green-500' : 'text-red-500'}>
                ● {image.gemini_processing.success ? 'Text extraction successful' : 'Text extraction failed'}
              </p>
              {image.gemini_processing.error && (
                <p className="text-red-500">Error: {image.gemini_processing.error}</p>
              )}
              {image.gemini_processing.processing_time && (
                <p>Processing attempts: {image.gemini_processing.processing_time}</p>
              )}
            </div>
          ) : (
            <p className="text-yellow-500">● Processing status unknown</p>
          )}
        </div>
      </div>
      
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            Extracted Text:
          </label>
          {image.extracted_text && (
            <button
              onClick={() => onViewText(image, `${title} #${index + 1}`)}
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
          {image.extracted_text ? (
            <div>
              <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed line-clamp-4">
                {image.extracted_text.length > 200 
                  ? `${image.extracted_text.substring(0, 200)}...`
                  : image.extracted_text
                }
              </pre>
              {image.extracted_text.length > 200 && (
                <button
                  onClick={() => onViewText(image, `${title} #${index + 1}`)}
                  className={`mt-2 text-xs underline ${
                    isDark ? 'text-cyan-400 hover:text-cyan-300' : 'text-blue-500 hover:text-blue-600'
                  }`}
                >
                  View full text ({image.extracted_text.length} characters)
                </button>
              )}
            </div>
          ) : (
            <p className={`italic ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              {image.gemini_processing?.success === false 
                ? 'Text extraction failed' 
                : 'No text extracted or processing in progress...'}
            </p>
          )}
        </div>
      </div>
    </div>
  </div>
);

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
      
      <div className="space-y-8">
        {/* Main Images Data */}
        {mainImages.length > 0 && (
          <div>
            <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
              Util Screenshots Data
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {mainImages.map((image, index) => (
                <ImageCard
                  key={`main-data-${index}`}
                  image={image}
                  index={index}
                  title="Util Screenshot"
                  isDark={isDark}
                  onViewText={handleViewText}
                />
              ))}
            </div>
          </div>
        )}

        {/* Secondary Images Data */}
        {secondaryImages.length > 0 && (
          <div>
            <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
              Website Screenshots Data
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {secondaryImages.map((image, index) => (
                <ImageCard
                  key={`secondary-data-${index}`}
                  image={image}
                  index={index}
                  title="Website Screenshot"
                  isDark={isDark}
                  onViewText={handleViewText}
                />
              ))}
            </div>
          </div>
        )}
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