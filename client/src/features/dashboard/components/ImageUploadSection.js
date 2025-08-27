import React, { useCallback } from 'react';
import { Upload, X, Image } from 'lucide-react';

const ImageUploadSection = ({ 
  title,
  images, 
  setImages, 
  isUploading, 
  setIsUploading,
  uploadImageHandler,
  uploadImageBase64Handler,
  inputId,
  isDark 
}) => {
  
  // File input handler - support multiple files
  const handleFileInput = useCallback((e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      if (file) {
        uploadImageHandler(file);
      }
    });
    // Clear the input so the same files can be selected again
    e.target.value = '';
  }, [uploadImageHandler]);

  // Drop handler - support multiple files
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => {
      if (file && file.type.startsWith('image/')) {
        uploadImageHandler(file);
      }
    });
  }, [uploadImageHandler]);

  // Paste handler
  const handlePaste = useCallback(async (e) => {
    e.preventDefault();
    const items = Array.from(e.clipboardData.items);
    
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const blob = item.getAsFile();
        if (blob) {
          setIsUploading(true);
          try {
            // Convert blob to base64
            const reader = new FileReader();
            reader.onload = async (e) => {
              const base64Data = e.target.result;
              const filename = `${title.toLowerCase().replace(/\s+/g, '-')}-pasted-${Date.now()}.png`;
              
              await uploadImageBase64Handler(base64Data, filename);
              setIsUploading(false);
            };
            reader.readAsDataURL(blob);
            
          } catch (error) {
            console.error(`${title} image paste upload failed:`, error);
            alert(`${title} image paste upload failed: ${error.message}`);
            setIsUploading(false);
          }
        }
        break;
      }
    }
  }, [title, uploadImageBase64Handler, setIsUploading]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  // Remove image by index
  const removeImage = useCallback((index) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  }, [setImages]);

  return (
    <div className="flex flex-col space-y-3">
      <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
        {title}
      </label>
      
      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer focus:outline-none focus:ring-2 ${
          isDark 
            ? 'border-gray-600 hover:border-gray-500 bg-gray-800 focus:ring-cyan-500' 
            : 'border-gray-300 hover:border-gray-400 bg-white focus:ring-blue-500'
        } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onPaste={handlePaste}
        onClick={() => !isUploading && document.getElementById(inputId).click()}
        tabIndex={0}
      >
        <Upload className={`mx-auto h-12 w-12 ${isDark ? 'text-gray-500' : 'text-gray-400'} ${isUploading ? 'animate-pulse' : ''}`} />
        <div className="mt-4">
          <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
            {isUploading ? (
              <span className="font-medium">Uploading {title.toLowerCase()}...</span>
            ) : (
              <>
                <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>Click to upload</span>, drag and drop, or <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>paste (Ctrl+V)</span>
              </>
            )}
          </p>
          <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>PNG, JPG, GIF up to 10MB</p>
        </div>
        
        <input
          id={inputId}
          type="file"
          className="hidden"
          accept="image/*"
          multiple
          onChange={handleFileInput}
          disabled={isUploading}
        />
      </div>

      {/* Display uploaded images */}
      {images.length > 0 && (
        <div className="grid grid-cols-1 gap-3">
          {images.map((image, index) => (
            <div key={`${inputId}-${index}`} className={`relative border rounded-lg p-4 ${
              isDark 
                ? 'border-gray-600 bg-gray-800' 
                : 'border-gray-200 bg-white'
            }`}>
              <button
                onClick={() => removeImage(index)}
                className={`absolute top-2 right-2 z-10 p-1 rounded-full transition-colors ${
                  isDark 
                    ? 'bg-red-900 hover:bg-red-800 text-red-400' 
                    : 'bg-red-100 hover:bg-red-200 text-red-600'
                }`}
              >
                <X size={16} />
              </button>
              
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <img
                    src={image.url}
                    alt={image.name}
                    className="h-20 w-20 object-cover rounded border"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium truncate ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
                    {image.name}
                  </p>
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {(image.file_size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  {image.upload_id && (
                    <p className={`text-xs ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                      ✓ {title} uploaded successfully
                    </p>
                  )}
                </div>
                <div className="flex-shrink-0">
                  <Image className={`h-5 w-5 ${isDark ? 'text-green-400' : 'text-green-500'}`} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ImageUploadSection;